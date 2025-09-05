# Risiko2Py – Client Anleitung (Deutsch)

## Voraussetzungen

- Python 3.8 oder neuer
- Internetverbindung (für Serverzugriff)
- Keine weiteren Programme nötig – alle Abhängigkeiten werden beim Start automatisch installiert.

## Client starten

1. Öffne ein Terminal und wechsle in das Verzeichnis:
   ```
   cd /Installationspfad/client
   ```

2. Starte den Client:
   ```
   python main.py
   ```

   Beim ersten Start werden automatisch alle benötigten Python-Bibliotheken installiert.

## Anmeldung & Verbindung

1. Gib die Server-Adresse ein (Standard: `http://localhost:5000/api`).
2. Melde dich mit deinem Benutzernamen und Passwort an oder registriere einen neuen Account.

## Neues Spiel starten

1. Klicke auf **"Start New Game"**.
2. Gib die gewünschten Einstellungen ein:
   - Anzahl der Galaxien
   - Anzahl der Planeten pro Galaxie
   - Spielernamen (durch Kommas getrennt, z.B. `Alice, Bob, Carol`)
   - Optional: Wähle für jeden Spieler eine Farbe aus.
3. Bestätige mit **OK**. Das Spiel wird auf dem Server erstellt.

## Spiel laden

1. Klicke auf **"Load Game"**.
2. Wähle ein vorhandenes Spiel aus der Liste aus und lade es.

## Spieloberfläche

- **Planeten**: Jeder Spieler besitzt zu Beginn einen Planeten. Die Farbe zeigt den Besitzer.
- **Flotten senden**: Wähle einen eigenen Planeten, gib das Ziel und die Anzahl der Schiffe ein.
- **Rundenende**: Klicke auf **"Declare Readiness"**. Die Runde endet, wenn alle Spieler bereit sind.
- **Jahr**: Das aktuelle Spieljahr wird oben angezeigt.

## Hinweise

- Du kannst jederzeit das Spiel speichern oder laden.
- Mit **"Delete All Games"** können alle gespeicherten Spiele gelöscht werden (nur Spiele, nicht Benutzerkonten).
- Die Navigation zwischen Galaxien erfolgt über die Pfeiltasten oder die Buttons.

## Fehlerbehebung

- Falls beim Start ein Fehler auftritt, prüfe, ob der Server läuft und erreichbar ist.
- Bei Problemen mit der Anmeldung: Stelle sicher, dass Benutzername und Passwort korrekt sind.

---

Viel Spaß beim Spielen von Risiko2Py!