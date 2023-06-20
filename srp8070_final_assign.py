import datetime as dt
import sqlite3
import sys
import time
import random
import os
import asyncio
import datetime
from metaapi_cloud_sdk import MetaApi

total_lots = 100
duration_between_trades_in_seconds = 5
duration_between_trades_in_mins = duration_between_trades_in_seconds / 60
duration_between_execution_sets_in_seconds = 10
duration_between_TWAP_execution_in_seconds = 1 * 60
number_of_exit_trades = 30
carry_over_from_previous_set = 0
duration_before_second_phase_in_seconds = 15
duration_before_third_phase_in_seconds = 15
third_phase_max_tries = 100
execution_sets = [
    {'start': {'hour': 18, 'min': 37, 'sec': 0},
     'end': {'hour': 18, 'min': 37, 'sec': 40},
     'lots': 0.25 * total_lots},
    {'start': {'hour': 18, 'min': 38, 'sec': 30},
     'end': {'hour': 18, 'min': 38, 'sec': 10},
     'lots': 0.25 * total_lots},
    {'start': {'hour': 18, 'min': 39, 'sec': 40},
     'end': {'hour': 18, 'min': 40, 'sec': 10},
     'lots': 0.25 * total_lots},
    {'start': {'hour': 18, 'min': 41, 'sec': 40},
     'end': {'hour': 18, 'min': 42, 'sec': 30},
     'lots': 0.25 * total_lots},
]
connection = None
account = None
currencies = ['EURUSD', 'USDJPY']
currency_meta = {'EURUSD': {'name': 'GBPUSD', 'total_quantity': total_lots, 'pending': total_lots, 'executed_qty': 0,
                            'average_price': None, 'is_trade_taken': False,
                            'total_expense': 0, 'trade_type': 'Short', 'carry_over_from_previous_set': 0},
                 'USDJPY': {'name': 'USDJPY', 'total_quantity': total_lots, 'pending': total_lots, 'executed_qty': 0,
                            'average_price': None, 'is_trade_taken': False,
                            'total_expense': 0, 'trade_type': 'Long', 'carry_over_from_previous_set': 0}}


async def get_connection_to_mt4():
    global connection, account
    token = os.getenv(
        'TOKEN') or 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJiOWY5MjcxMjE0ZjMyMDM1MDk1OWU5MGJiYzJhZjI3OSIsInBlcm1pc3Npb25zIjpbXSwidG9rZW5JZCI6IjIwMjEwMjEzIiwiaW1wZXJzb25hdGVkIjpmYWxzZSwicmVhbFVzZXJJZCI6ImI5ZjkyNzEyMTRmMzIwMzUwOTU5ZTkwYmJjMmFmMjc5IiwiaWF0IjoxNjgxOTU4NjA2fQ.oPNf5BA1aUlhFD-_D2dnGnEBAW96u9BJDIMzgvT8YnVa4eieRhcM_arXDggcezsqBc5ithQQ8fXazhZ_XouHWbeMpSVNXNiKzp7j9UUwru8uwzG00siuo8FUfjTFzQNKqdOc4AD0RFvTT41EnJR6JR34DtKmwc6vmNH_1fqAl4vXTyfY7KZEZhXTmcIkgc9K7Bbg4FQEXUyojywU6kr5mX2hBXvP46fC9qEIk_lX7o4O6gmy4LqpfeyTWeJQg6NRxS42nR_lEVJSSdXPlCOxSZSgX9gN7v4FrE6ZkCzcmhzFUHiPUowg4m3VUXyNe5BW_HzO-bTjRENGG7U3dwvHG8TblaZOterZHobh0oFyKH5LNp_PtZd8qJ6vFnL1-PkivDe9RG9oawZhEBsLZ6WRJ8oik-VIMVRvjmRR-2J6phAds3O51tvpYQfFqXG4J4jJi51mgNFRwTcub-ztM-FKdLuwHNkBlt1Lt7UcCCa29ujutSAlEtcNyNb_p8oYkhDk1R_pdYyP-FiNDzo69VegQuzkmG3z6twukLBDH5NYxkq73b2vnuMUyKkhrwSm9rEuVS09vMqHuUuVWGH1BoT2eleOpbcJiZy4nePoMex1lydfYE7ohXorMMP96aFoG9BisAJ2-PhglxZwwqjxfSUt8_7xJdIwV_bilw0qz1aGDMQ'
    accountId = os.getenv('ACCOUNT_ID') or 'e5985df9-e74a-45d6-86b0-2a56902b2e01'

    api = MetaApi(token)
    account = await api.metatrader_account_api.get_account(accountId)
    initial_state = account.state
    deployed_states = ['DEPLOYING', 'DEPLOYED']

    if initial_state not in deployed_states:
        #  wait until account is deployed and connected to broker
        print('Deploying account')
        await account.deploy()

    print('Waiting for API server to connect to broker (may take couple of minutes)')
    await account.wait_connected()

    # connect to MetaApi API
    connection = account.get_rpc_connection()
    await connection.connect()

    # wait until terminal state synchronized to the local state
    print('Waiting for SDK to synchronize to terminal state (may take some time depending on your history size)')
    await connection.wait_synchronized()

    # invoke RPC API (replace ticket numbers with actual ticket numbers which exist in your MT account)
    print('Testing MetaAPI RPC API')
    print('account information:', await connection.get_account_information())
    print('positions:', await connection.get_positions())
    return connection, account


async def get_current_rate(currency):
    global connection, currency_meta
    latest_market_price = await connection.get_symbol_price(currency)
    trade_type = currency_meta[currency]['trade_type']
    return latest_market_price['ask'] if trade_type == 'Long' else latest_market_price['bid']


def cannot_trade(currency, current_rate):
    global currency_meta
    average_price = currency_meta[currency]['average_price']
    trade_type = currency_meta[currency]['trade_type']
    if average_price is None:
        return False
    return (trade_type == 'Long' and current_rate < average_price) or (
            trade_type == 'Short' and current_rate > average_price)


async def trade(currency, lots):
    global connection, currency_meta
    trade_type = currency_meta[currency]['trade_type']
    average_price = currency_meta[currency]['average_price']
    print("{} {} for {} volume".format(currency, trade_type, str(lots)))
    print("Average is {}".format(str(average_price)))

    current_rate = await get_current_rate(currency)
    if cannot_trade(currency, current_rate):
        print("Cannot trade since current price {} does not meet condition with average price {}".format(
            str(current_rate), str(average_price)))
        return {'status': False, 'price': 0, 'quantity': 0}
    transaction = {'pair': currency, 'trade_type': None, 'quantity': lots, 'rate': current_rate,
                   'average': currency_meta[currency]['average_price']}
    try:
        print("VOLUME = " + str(lots))
        if trade_type == 'Long':
            trade_info = await connection.create_market_buy_order(currency, lots)
            transaction['trade_type'] = 'Long'
        else:
            trade_info = await connection.create_market_sell_order(currency, lots)
            transaction['trade_type'] = 'Short'
        print(trade_info)
        write_to_db(transaction)
        return {'status': True, 'price': current_rate, 'quantity': lots}
    except Exception as err:
        print('Trade failed with error:' + str(err))
        return {'status': False, 'price': 0, 'quantity': 0}


def clean_extraction_sets():
    global currencies
    for current_set in execution_sets:
        start = current_set['start']
        end = current_set['end']
        current_set['start'] = dt.datetime.now().replace(hour=start['hour'], minute=start['min'],
                                                         second=start['sec'], microsecond=0)
        current_set['end'] = dt.datetime.now().replace(hour=end['hour'], minute=end['min'],
                                                       second=end['sec'], microsecond=0)
        if current_set['end'] < current_set['start']:
            current_set['end'] = current_set['end'] + dt.timedelta(days=1)
        current_set['count'] = (
                (current_set['end'] - current_set['start']) / duration_between_trades_in_seconds).seconds
        for currency in currencies:
            current_set[currency] = {'lots': current_set['lots'], 'pending': 0}


async def trade_execution_sets():
    global currency_meta, connection, account, currencies
    for current_set in execution_sets:
        while dt.datetime.now() < current_set['start']:
            print(dt.datetime.now())
            time.sleep(1)
        if current_set['start'] <= dt.datetime.now() <= current_set['end']:
            for currency in currencies:
                current_currency_set = current_set[currency]
                current_currency_set['lots'] += currency_meta[currency]['carry_over_from_previous_set']
                current_currency_set['pending'] = current_currency_set['lots']
                current_currency_set['trade_lots_per_trade'] = current_currency_set['lots'] / current_set['count']
            for i in range(current_set['count']):
                await get_connection_to_mt4()
                for currency in currencies:
                    current_currency_set = current_set[currency]
                    try:
                        trade_info = await trade(currency, current_currency_set['trade_lots_per_trade'])
                        if trade_info['status']:
                            trade_expense = trade_info['price'] * trade_info['quantity']
                            currency_meta[currency]['total_expense'] += trade_expense
                            currency_meta[currency]['executed_qty'] += trade_info['quantity']
                            current_currency_set['pending'] -= trade_info['quantity']
                    except Exception as err:
                        print('Exception' + str(err))
                # await connection.close()
                # await account.undeploy()
                time.sleep(duration_between_trades_in_seconds)
            print(current_set)
            for currency in currencies:
                current_currency_set = current_set[currency]
                currency_meta[currency]['carry_over_from_previous_set'] = current_currency_set['pending']
                currency_meta[currency]['average_price'] = currency_meta[currency]['total_expense'] / \
                                                           currency_meta[currency]['executed_qty']
        time.sleep(duration_between_execution_sets_in_seconds)


async def second_phase():
    global currency_meta, currencies, connection, account
    time.sleep(duration_before_second_phase_in_seconds)
    #await get_connection_to_mt4()
    for currency in currencies:
        try:
            trade_info = await trade(currency, currency_meta[currency]['carry_over_from_previous_set'] / 2)
            currency_meta[currency]['is_trade_taken'] = trade_info['status']
            currency_meta[currency]['carry_over_from_previous_set'] /= 2 if currency_meta[currency][
                'is_trade_taken'] else 1
        except Exception as err:
            print('Exception ' + str(err))
    await connection.close()
    await account.undeploy()


async def third_phase():
    global connection, account, number_of_exit_trades, currencies, currency_meta, third_phase_max_tries
    time.sleep(duration_before_third_phase_in_seconds)
    #await get_connection_to_mt4()
    for currency in currencies:
        if currency_meta[currency]['is_trade_taken']:
            await trade(currency, currency_meta[currency]['carry_over_from_previous_set'])
        elif currency_meta[currency]['executed_qty'] / currency_meta[currency]['total_quantity'] <= 0.75:
            current_rate = await get_current_rate(currency)
            if cannot_trade(currency, current_rate):
                print("Exiting position {} till 20%".format(currency_meta[currency]['total_quantity']))
                volume_to_be_exited = currency_meta[currency]['executed_qty'] - total_lots * 0.2
                volume_per_exit_trade = volume_to_be_exited / number_of_exit_trades

                while currency_meta[currency]['executed_qty'] > total_lots * 0.2 and third_phase_max_tries > 0:
                    third_phase_max_tries -= 1
                    positions = await connection.get_positions()
                    positions = [item for item in positions if item['symbol'] == currency]
                    latest_position = positions[0]
                    print(latest_position)
                    latest_position_id = latest_position['id']
                    latest_position_vol = latest_position['volume']
                    exit_vol = min(latest_position_vol, volume_per_exit_trade)
                    try:
                        await connection.close_position_partially(latest_position_id, exit_vol)
                        currency_meta[currency]['executed_qty'] -= volume_per_exit_trade
                        transaction = {'pair': currency, 'trade_type': 'Short' if currency_meta[currency][
                                                                                      'trade_type'] == 'Long' else 'Long',
                                       'quantity': exit_vol, 'rate': current_rate,
                                       'average': currency_meta[currency]['average_price']}
                        write_to_db(transaction)
                    except Exception as err:
                        print(str(err))
                time.sleep(duration_between_TWAP_execution_in_seconds)

    await connection.close()
    await account.undeploy()


async def trade_smart():
    global connection, account
    initialize_db()
    connection, account = await get_connection_to_mt4()
    clean_extraction_sets()
    await trade_execution_sets()
    await second_phase()
    await third_phase()
    # for currency in currencies:
    #     current_rate = await get_current_rate(currency)
    #     print(current_rate)
    await connection.close()
    await account.undeploy()


def get_connection_to_db():
    sqlite_file = 'DEMO.db'
    conn = sqlite3.connect(sqlite_file)
    return conn


def initialize_db():
    conn = get_connection_to_db()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS TRANSACTIONS (
        CREATED_TIME int,
        CURRENCY_PAIR text,
        TRADE_TYPE text,
        QUANTITY float,
        RATE float,
        AVERAGE float);
        ''')


def write_to_db(transaction):
    conn = get_connection_to_db()
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO TRANSACTIONS VALUES ('{}', '{}', '{}', '{}', '{}', '{}');'''.format(
        dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), transaction['pair'], transaction['trade_type'],
        transaction['quantity'], transaction['rate'], transaction['average']))
    conn.commit()
    print(transaction)


asyncio.run(trade_smart())
