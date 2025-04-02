# py-networked-game

## Overview
`py-networked-game` is a multiplayer networked game built using Python. This project allows players to join a game hosted on a server, enabling real-time interaction and gameplay from different networks.

## Project Structure
```
py-networked-game
├── client
│   ├── main.py          # Entry point for the client application
│   └── game_client.py   # Contains the GameClient class for managing client-server interactions
├── server
│   ├── main.py          # Entry point for the server application
│   └── game_server.py   # Contains the GameServer class for managing game sessions and player connections
├── shared
│   └── utils.py         # Utility functions and constants shared between client and server
├── requirements.txt      # Lists the dependencies required for the project
└── README.md             # Documentation for the project
```

## Setup Instructions
1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd py-networked-game
   ```

2. **Install dependencies:**
   Ensure you have Python installed, then run:
   ```
   pip install -r requirements.txt
   ```

## Usage
### Running the Server
To start the server, navigate to the `server` directory and run:
```
python main.py
```
The server will listen for incoming connections from clients.

### Running the Client
To start the client, navigate to the `client` directory and run:
```
python main.py
```
Follow the prompts to connect to the server and join a game.

## Game Mechanics
- Players can join a game hosted on the server.
- The server manages game sessions and player interactions.
- Players can perform actions that are communicated to the server, which updates the game state and broadcasts changes to all connected clients.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.