import json
from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.models import GameState, User
from database import db
from utils.security import create_game_state, validate_game_state

game_bp = Blueprint('game', __name__)

@game_bp.route('/game/start', methods=['POST'])
@jwt_required()
def start_game():
    import random
    data = request.get_json()
    if not data or 'players' not in data:
        return jsonify({'msg': 'Missing players data'}), 400

    players = data['players']
    galaxies = data.get('galaxies', 1)
    planets = data.get('planets', 80)
    user_id = get_jwt_identity()
    player_colors = data.get('colors')

    # Assign a color to each player (use provided or generate)
    if player_colors and len(player_colors) == len(players):
        owner_colors = {player: color for player, color in zip(players, player_colors)}
    else:
        owner_colors = {player: "#{:06X}".format(random.randint(0, 0xFFFFFF)) for player in players}

    # --- Generate button coordinates for each galaxy ---
    rows, cols = 40, 15
    galaxy_button_coords = {}
    for galaxy_index in range(galaxies):
        positions = [(row, col) for row in range(rows) for col in range(cols)]
        random.shuffle(positions)
        button_coords = {}
        for i in range(planets):
            button_coords[i+1] = positions[i]
        galaxy_button_coords[galaxy_index] = button_coords

    # --- Assign each player a starting planet in a different galaxy ---
    # Cycle through galaxies if there are more players than galaxies
    player_start_planets = {}
    for idx, player in enumerate(players):
        galaxy_index = idx % galaxies
        # Pick a random system in this galaxy for the player
        system_ids = list(range(1, planets + 1))
        random.shuffle(system_ids)
        chosen_sys = system_ids[0]
        player_start_planets[player] = (galaxy_index, chosen_sys)

    systems = []
    for galaxy_index in range(galaxies):
        for sys_id in range(1, planets + 1):
            owner = None
            current_ships = 0
            ship_production = random.randint(1, 10)
            defense_factor = round(random.uniform(0.7, 1.0), 2)
            for player, (g_idx, s_id) in player_start_planets.items():
                if galaxy_index == g_idx and sys_id == s_id:
                    owner = player
                    current_ships = 250
                    ship_production = 10
                    defense_factor = 1.0
            coords = galaxy_button_coords[galaxy_index][sys_id]
            systems.append({
                "galaxy": galaxy_index,
                "system_id": sys_id,
                "owner": owner,
                "current_ships": current_ships,
                "ship_production": ship_production,
                "defense_factor": defense_factor,
                "coords": coords
            })

    state = {
        "galaxies": galaxies,
        "planets": planets,
        "systems": systems,
        "fleets": [],
        "year": 1,
        "button_coords": galaxy_button_coords,
        "owner_colors": owner_colors
    }
    game_state = GameState(
        user_id=user_id,
        players=json.dumps(players),
        state=json.dumps(state)
    )
    db.session.add(game_state)
    db.session.commit()

    return jsonify({'msg': 'Game started', 'game_id': game_state.id}), 201

@game_bp.route('/game/save', methods=['POST'])
@jwt_required()
def save_game():
    data = request.get_json()
    if not data or 'game_id' not in data or 'state' not in data or 'players' not in data:
        return jsonify({'msg': 'Missing game_id, state, or players data'}), 400

    game_state = GameState.query.get(data['game_id'])
    if not game_state:
        return jsonify({'msg': 'Game not found'}), 404

    game_state.state = json.dumps(data['state'])
    game_state.players = json.dumps(data['players'])
    db.session.commit()

    return jsonify({'msg': 'Game state saved'}), 200

@game_bp.route('/game/<int:game_id>', methods=['GET'])
@jwt_required()
def get_game_info(game_id):
    game_state = GameState.query.get(game_id)
    if not game_state:
        return jsonify({'msg': 'Game not found'}), 404
    
    return jsonify({
        'game_id': game_state.id,
        'players': game_state.players,
        'state': game_state.state
    }), 200

@game_bp.route('/game/send_fleet', methods=['POST'])
@jwt_required()
def send_fleet():
    data = request.get_json()
    game_id = data.get("game_id")
    source = data.get("source")
    destination = data.get("destination")
    ships = data.get("ships")
    owner = data.get("owner")
    if not all([game_id, source, destination, ships, owner]):
        return jsonify({'msg': 'Missing fleet data'}), 400

    game_state = GameState.query.get(game_id)
    if not game_state:
        return jsonify({'msg': 'Game not found'}), 404
    state = json.loads(game_state.state)

    # Find the galaxy for source and destination systems
    systems = state["systems"]
    source_sys = next((s for s in systems if s["system_id"] == source and s["owner"] == owner), None)
    dest_sys = next((s for s in systems if s["system_id"] == destination), None)
    if not source_sys or not dest_sys:
        return jsonify({'msg': 'Invalid source or destination'}), 400

    source_galaxy = source_sys["galaxy"]
    dest_galaxy = dest_sys["galaxy"]

    button_coords = state.get("button_coords", {})
    # Get the coordinates from the correct galaxy
    pos1 = button_coords.get(str(source_galaxy), {}).get(str(source)) \
        or button_coords.get(source_galaxy, {}).get(source)
    pos2 = button_coords.get(str(dest_galaxy), {}).get(str(destination)) \
        or button_coords.get(dest_galaxy, {}).get(destination)
    if not pos1 or not pos2:
        return jsonify({'msg': 'Invalid source or destination'}), 400

    import math
    distance = math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    turns_required = max(1, int(round(distance)))

    # Deduct ships from source system
    if source_sys["current_ships"] < ships:
        return jsonify({'msg': 'Not enough ships!'}), 400
    source_sys["current_ships"] -= ships

    # Add fleet to state
    fleet = {
        "source": source,
        "destination": destination,
        "ships": ships,
        "owner": owner,
        "turns": turns_required,
        "source_galaxy": source_galaxy,
        "dest_galaxy": dest_galaxy
    }
    state.setdefault("fleets", []).append(fleet)
    game_state.state = json.dumps(state)
    db.session.commit()
    return jsonify({'state': game_state.state}), 200

@game_bp.route('/game/ready', methods=['POST'])
@jwt_required()
def player_ready():
    data = request.get_json()
    game_id = data.get("game_id")
    player = data.get("player")
    if not game_id or not player:
        return jsonify({'msg': 'Missing game_id or player'}), 400

    game_state = GameState.query.get(game_id)
    if not game_state:
        return jsonify({'msg': 'Game not found'}), 404
    state = json.loads(game_state.state)
    players = json.loads(game_state.players)

    # Mark player as ready
    for p in players:
        if (isinstance(p, dict) and p.get("owner") == player) or (isinstance(p, str) and p == player):
            if isinstance(p, dict):
                p["ready"] = True
            else:
                # If player is a string, convert to dict
                idx = players.index(p)
                players[idx] = {"owner": p, "ready": True}
            break

    # Check if all players are ready
    all_ready = all((p.get("ready") if isinstance(p, dict) else False) for p in players)
    if all_ready:
        # --- Process fleets ---
        systems = state["systems"]
        fleets = state.get("fleets", [])
        fleets_to_remove = []
        for fleet in fleets:
            fleet["turns"] -= 1
            if fleet["turns"] <= 0:
                # Find destination system
                dest = next((s for s in systems if s["system_id"] == fleet["destination"] and s["galaxy"] == systems[0]["galaxy"]), None)
                if not dest:
                    continue
                # If unowned or same owner, add ships and set owner
                if dest["owner"] == fleet["owner"] or dest["owner"] is None:
                    dest["current_ships"] += fleet["ships"]
                    dest["owner"] = fleet["owner"]
                else:
                    # Combat: more ships wins
                    if fleet["ships"] > dest["current_ships"]:
                        dest["owner"] = fleet["owner"]
                        dest["current_ships"] = fleet["ships"] - dest["current_ships"]
                    else:
                        dest["current_ships"] -= fleet["ships"]
                fleets_to_remove.append(fleet)
        # Remove processed fleets
        state["fleets"] = [f for f in fleets if f not in fleets_to_remove]

        # --- Production phase ---
        for sys in systems:
            if sys["owner"]:
                sys["current_ships"] += sys["ship_production"]

        # --- Advance year ---
        state["year"] = state.get("year", 1) + 1

        # --- Reset readiness ---
        for p in players:
            if isinstance(p, dict):
                p["ready"] = False

    # Save updated state and players
    game_state.state = json.dumps(state)
    game_state.players = json.dumps(players)
    db.session.commit()
    return jsonify({'state': game_state.state}), 200

@game_bp.route('/game/list', methods=['GET'])
@jwt_required()
def list_games():
    games = GameState.query.all()
    result = []
    for game in games:
        players = json.loads(game.players)
        # Each player dict should have 'owner' and 'ready'
        result.append({
            "game_id": game.id,
            "players": players
        })
    return jsonify(result), 200

@game_bp.route('/game/delete_all', methods=['POST'])
@jwt_required()
def delete_all_games():
    # Only allow if the user is an admin or add your own check if needed
    GameState.query.delete()
    db.session.commit()
    return jsonify({'msg': 'All games deleted.'}), 200


