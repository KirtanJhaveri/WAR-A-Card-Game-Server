# WAR: A Card Game Server

This repository contains a server implementation for the "War" card game. The server manages game sessions between multiple clients following a defined network protocol.

## Introduction

The "War" card game is a simplified version where players receive half of a shuffled deck, take turns playing cards, and compare them to determine wins, losses, or draws. The primary objective of this project is to implement a server that orchestrates gameplay between connected clients adhering to the specified protocol.

## Project Structure

The project includes a single `war.py` file that contains both the server and client implementations. The server is responsible for managing incoming connections, pairing clients, and coordinating game sessions, while the client connects to the server to participate in the game.

## Features

### Server Functionality
- **Connection Handling**: Listens for incoming TCP connections on a specified port.
- **Game Pairing**: Paired connected clients to engage in a game of "War."
- **Multiple Game Support**: Allows simultaneous gameplay between different pairs of clients.
- **Error Handling**: Detects incorrect client behavior, closes connections, and maintains server stability.

### Client Interaction
- **Client-Server Communication**: Clients exchange messages with the server following the defined "War" protocol.
- **Gameplay Management**: Initiates card plays, receives game results, and manages the game state accordingly.

### Efficiency

#### Simultaneous Game Handling
The server efficiently manages multiple concurrent games by employing asynchronous I/O operations provided by the asyncio library in Python. This allows for non-blocking I/O and seamless handling of multiple client connections, ensuring optimal performance even when handling multiple game sessions simultaneously.

#### Error Handling and Stability
Efficient error detection mechanisms are implemented to handle incorrect client behavior gracefully. In case of erroneous messages or unexpected client actions, the server promptly terminates the affected game session while maintaining stability for other ongoing games.

## How to Use

### Server

Run the server using the following command:

```bash
python war.py server <host> <port>```