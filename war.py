"""
war card game client and server
"""
import asyncio
from collections import namedtuple
from enum import Enum
import logging
import random
# import socket
# import socketserver
# import _thread
import sys

paired_clients = []

"""
Namedtuples work like classes, but are much more lightweight so they end
up being faster. It would be a good idea to keep objects in each of these
for each game which contain the game's state, for instance things like the
socket, the cards given, the cards still available, etc.
"""
Game = namedtuple("Game", ["p1", "p2"])


class Command(Enum):
    """
    The byte values sent as the first byte of any message in the war protocol.
    """
    WANTGAME = 0
    GAMESTART = 1
    PLAYCARD = 2
    PLAYRESULT = 3


class Result(Enum):
    """
    The byte values sent as the payload byte of a PLAYRESULT message.
    """
    WIN = 0
    DRAW = 1
    LOSE = 2


def readexactly(sock, num_of_bytes):
    """
    Accumulate exactly `numbytes` from `sock` and return those. If EOF is found
    before numbytes have been received, be sure to account for that here or in
    the caller.
    """

    data = b''
    while len(data) != num_of_bytes:
        current = sock.recv(1)
        data += current
        if len(current) == 0 and len(data) != num_of_bytes:
            logging.error('THERE IS AN ERROR.')
            sock.close()
            return data

    return data


def kill_game(s_1, s_2):
    """
    TODO: If either client sends a bad message, immediately nuke the game.
    """
    s_1.close()
    s_2.close()
    # pass


def compare_cards(card1, card2):
    """
    TODO: Given an integer card representation, return -1 for card1 < card2,
    0 for card1 = card2, and 1 for card1 > card2
    """
    first_card = card1 % 13
    second_card = card2 % 13

    # Return values changed here to match "RESULTS"
    if first_card < second_card:
        return 2
    if first_card == second_card:
        return 1

    return 0


def deal_cards():
    """
    TODO: Randomize a deck of cards (list of ints 0..51), and return two
    26 card "hands."
    """

    deck_size = 52
    deck = list(range(deck_size))
    random.shuffle(deck)
    first_hand = []
    second_hand = []

    # Probably more efficient ways of doing this (slicing)
    while len(deck) > 0:
        dealt_card = deck.pop()
        if len(first_hand) < 26:
            first_hand.append(dealt_card)
        else:
            second_hand.append(dealt_card)

    both_hands = [first_hand, second_hand]
    return both_hands


def check_card(card, deck):
    """ check a card"""
    if card not in deck:
        return False
    return True


def kill(first_client, second_client):
    """
    Kill a client connection
    """
    kill_game(first_client[1], second_client[1])
    kill_game(first_client[1].get_extra_info('socket'),
              second_client[1].get_extra_info('socket'))


async def handle_game(first_client, second_client):
    """
    This is the main component of the game.
    first_client and second_client are
    2 client sockets that connected as a pair
    They play the game here and the error checking is done here
    """

    split_deck = deal_cards()
    client1_cards = split_deck[0]
    client2_cards = split_deck[1]

    client1_used = [False] * 26
    client2_used = [False] * 26

    try:
        first_client_data = await first_client[0].readexactly(2)
        second_client_data = await second_client[0].readexactly(2)

        if (first_client_data[1] != 0) or second_client_data[1] != 0:
            logging.error('ERROR... '
                          'User does not enter in 0 for the first time')
            kill(first_client, second_client)
            return

        # Clients are ready for their cards
        first_client[1].write(bytes(([Command.GAMESTART.value] +
                                     client1_cards)))
        second_client[1].write(bytes(([Command.GAMESTART.value] +
                                      client2_cards)))

        total_turns = 0

        while total_turns < 26:

            first_client_data = await first_client[0].readexactly(2)
            second_client_data = await second_client[0].readexactly(2)

            # Check if first byte was 'play card'
            if first_client_data[0] != 2 or second_client_data[0] != 2:
                logging.error('Error... User does not enter in 2.')
                kill(first_client, second_client)
                return

            # Check if card is in deck

            if check_card(first_client_data[1], split_deck[0]) is False \
                    or \
                    check_card(second_client_data[1], split_deck[1]) is False:
                logging.error('Error... '
                              'A clients card does not match card dealt')
                kill(first_client, second_client)
                return

            # Check if card was already used
            for card_no in range(0, 26):

                if first_client_data[1] == client1_cards[card_no] or \
                        second_client_data[1] == client2_cards[card_no]:

                    if client1_used[card_no] is False:
                        client1_used[card_no] = True

                    elif client2_used[card_no] is False:
                        client2_used[card_no] = True

                    else:
                        logging.error('Error: A client tried to use '
                                      'the same card again ')
                        kill(first_client, second_client)
                        return

            # Get the results for the first and second client
            client1_result = compare_cards(first_client_data[1],
                                           second_client_data[1])
            client2_result = compare_cards(second_client_data[1],
                                           first_client_data[1])

            # Concat the command to send with the result
            client1_send_result = [Command.PLAYRESULT.value, client1_result]
            client2_send_result = [Command.PLAYRESULT.value, client2_result]

            # Write back to the client
            first_client[1].write(bytes(client1_send_result))
            second_client[1].write(bytes(client2_send_result))

            total_turns += 1

        kill(first_client, second_client)

    except ConnectionResetError:
        logging.error("ConnectionResetError")

    except asyncio.streams.IncompleteReadError:
        logging.error("asyncio.streams.IncompleteReadError")

    except OSError:
        logging.error("OSError")

    return 0


async def pair_clients(reader, writer):
    """
    For every client that it connects, it waits until a 2nd client
    connects to "pair" the clients up, then it sends them off to
    their game.
    """

    # List of Tuples where tuples are paired clients
    # Here clients[0] and clients[1] are 2 separate clients
    temp_paired_clients = paired_clients
    for clients in temp_paired_clients:
        if clients[1] is None:
            clients[1] = (reader, writer)
            await handle_game(clients[0], clients[1])
            clients[0][1].close()
            clients[1][1].close()
            paired_clients.remove(clients)
            return

    paired_clients.append([(reader, writer), None])


def serve_game(host, port):
    """
    Runs an asyncio event loop for every client that it connects.
    Will run forever until server presses control+c.
    """

    loop = asyncio.get_event_loop()
    co_routine = asyncio.start_server(pair_clients, host, port, loop=loop)

    server = loop.run_until_complete(co_routine)

    # logs ip address and port number where server is being served
    logging.info('Serving on %s', server.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())

    loop.close()


async def limit_client(host, port, loop, sem):
    """
    Limit the number of clients currently executing.
    You do not need to change this function.
    """
    async with sem:
        return await client(host, port, loop)


async def client(host, port, loop):
    """
    Run an individual client on a given event loop.
    You do not need to change this function.
    """
    try:

        reader, writer = await asyncio.open_connection(host, port, loop=loop)
        # send want game
        myscore = 0

        writer.write(b"\0\0")
        card_msg = await reader.readexactly(27)

        for card in card_msg[1:]:

            writer.write(bytes([Command.PLAYCARD.value, card]))
            result = await reader.readexactly(2)

            if result[1] == Result.WIN.value:
                myscore += 1
            elif result[1] == Result.LOSE.value:
                myscore -= 1
        if myscore > 0:
            result = "won"
        elif myscore < 0:
            result = "lost"
        else:
            result = "drew"

        logging.debug("Result: %s", result)
        logging.debug("Game complete, I %s", result)
        writer.close()
        return 1
    except ConnectionResetError:
        logging.error("ConnectionResetError")
        return 0
    except asyncio.streams.IncompleteReadError:
        logging.error("asyncio.streams.IncompleteReadError")
        return 0
    except OSError:
        logging.error("OSError")
        return 0


def main(args):
    """
    launch a client/server
    """
    host = args[1]
    port = int(args[2])
    if args[0] == "server":
        try:
            serve_game(host, port)
        except KeyboardInterrupt:
            pass
        return
    loop = asyncio.get_event_loop()

    if args[0] == "client":
        loop.run_until_complete(client(host, port, loop))
    elif args[0] == "clients":
        sem = asyncio.Semaphore(1000)
        num_clients = int(args[3])
        clients = [limit_client(host, port, loop, sem)
                   for x in range(num_clients)]

        async def run_all_clients():
            """
            use `as_completed` to spawn all clients simultaneously
            and collect their results in arbitrary order.
            """
            completed_clients = 0
            for client_result in asyncio.as_completed(clients):
                completed_clients += await client_result
            return completed_clients

        res = loop.run_until_complete(
            asyncio.Task(run_all_clients(), loop=loop))
        logging.info("%d completed clients", res)

    loop.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    main(sys.argv[1:])
