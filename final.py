# import datetime as dt
# import sys
# import time
# import random
# import os
# import asyncio
# from metaapi_cloud_sdk import MetaApi
#
# total_lots = 100
# duration_between_trades_in_seconds = 15 * 60
# duration_between_trades_in_mins = duration_between_trades_in_seconds / 60
# duration_between_execution_sets_in_seconds = 10
# duration_between_TWAP_execution_in_seconds = 10
# number_of_exit_trades = 50
# carry_over_from_previous_set = 0
# duration_before_second_phase_in_seconds = 30 * 60
# duration_before_third_phase_in_seconds = 30 * 60
# total_expense = 0
# total_quantity = 0
# average_price = 1.25202
# is_trade_taken = None
# execution_sets = [
#     {'start': {'hour': 23, 'min': 0, 'sec': 0},
#      'end': {'hour': 1, 'min': 0, 'sec': 0},
#      'lots': 0.2 * total_lots},
#     {'start': {'hour': 3, 'min': 0, 'sec': 0},
#      'end': {'hour': 6, 'min': 0, 'sec': 0},
#      'lots': 0.3 * total_lots},
#     {'start': {'hour': 15, 'min': 0, 'sec': 0},
#      'end': {'hour': 17, 'min': 0, 'sec': 0},
#      'lots': 0.2 * total_lots},
#     {'start': {'hour': 19, 'min': 0, 'sec': 0},
#      'end': {'hour': 22, 'min': 0, 'sec': 0},
#      'lots': 0.3 * total_lots}
#     # {'start': {'hour': 3, 'min': 35, 'sec': 0},
#     #  'end': {'hour': 3, 'min': 36, 'sec': 34},
#     #  'lots': 0.5 * total_lots},
# ]
# CURRENCY = sys.argv[1]
# TRADE_TYPE = sys.argv[2]
# connection = None
# account = None
#
#
# async def get_connection_to_mt4():
#     token = os.getenv(
#         'TOKEN') or 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJiOWY5MjcxMjE0ZjMyMDM1MDk1OWU5MGJiYzJhZjI3OSIsInBlcm1pc3Npb25zIjpbXSwidG9rZW5JZCI6IjIwMjEwMjEzIiwiaW1wZXJzb25hdGVkIjpmYWxzZSwicmVhbFVzZXJJZCI6ImI5ZjkyNzEyMTRmMzIwMzUwOTU5ZTkwYmJjMmFmMjc5IiwiaWF0IjoxNjgxOTU4NjA2fQ.oPNf5BA1aUlhFD-_D2dnGnEBAW96u9BJDIMzgvT8YnVa4eieRhcM_arXDggcezsqBc5ithQQ8fXazhZ_XouHWbeMpSVNXNiKzp7j9UUwru8uwzG00siuo8FUfjTFzQNKqdOc4AD0RFvTT41EnJR6JR34DtKmwc6vmNH_1fqAl4vXTyfY7KZEZhXTmcIkgc9K7Bbg4FQEXUyojywU6kr5mX2hBXvP46fC9qEIk_lX7o4O6gmy4LqpfeyTWeJQg6NRxS42nR_lEVJSSdXPlCOxSZSgX9gN7v4FrE6ZkCzcmhzFUHiPUowg4m3VUXyNe5BW_HzO-bTjRENGG7U3dwvHG8TblaZOterZHobh0oFyKH5LNp_PtZd8qJ6vFnL1-PkivDe9RG9oawZhEBsLZ6WRJ8oik-VIMVRvjmRR-2J6phAds3O51tvpYQfFqXG4J4jJi51mgNFRwTcub-ztM-FKdLuwHNkBlt1Lt7UcCCa29ujutSAlEtcNyNb_p8oYkhDk1R_pdYyP-FiNDzo69VegQuzkmG3z6twukLBDH5NYxkq73b2vnuMUyKkhrwSm9rEuVS09vMqHuUuVWGH1BoT2eleOpbcJiZy4nePoMex1lydfYE7ohXorMMP96aFoG9BisAJ2-PhglxZwwqjxfSUt8_7xJdIwV_bilw0qz1aGDMQ'
#     accountId = os.getenv('ACCOUNT_ID') or 'e5985df9-e74a-45d6-86b0-2a56902b2e01'
#
#     api = MetaApi(token)
#     account = await api.metatrader_account_api.get_account(accountId)
#     initial_state = account.state
#     deployed_states = ['DEPLOYING', 'DEPLOYED']
#
#     if initial_state not in deployed_states:
#         #  wait until account is deployed and connected to broker
#         print('Deploying account')
#         await account.deploy()
#
#     print('Waiting for API server to connect to broker (may take couple of minutes)')
#     await account.wait_connected()
#
#     # connect to MetaApi API
#     mt4_connection = account.get_rpc_connection()
#     await mt4_connection.connect()
#
#     # wait until terminal state synchronized to the local state
#     print('Waiting for SDK to synchronize to terminal state (may take some time depending on your history size)')
#     await mt4_connection.wait_synchronized()
#
#     # invoke RPC API (replace ticket numbers with actual ticket numbers which exist in your MT account)
#     print('Testing MetaAPI RPC API')
#     print('account information:', await mt4_connection.get_account_information())
#     print('positions:', await mt4_connection.get_positions())
#     return mt4_connection, account
#
#
# async def check_if_connection_is_active():
#     global connection, account
#     print("CHECK")
#     # await connection.connect()
#
#
# async def get_current_rate():
#     global connection
#     await check_if_connection_is_active()
#     latest_market_price = await connection.get_symbol_price(CURRENCY)
#     return latest_market_price['ask'] if TRADE_TYPE == 'Long' else latest_market_price['bid']
#
#
# def cannot_trade(current_rate):
#     global average_price
#     if average_price is None:
#         return False
#     return (TRADE_TYPE == 'Long' and current_rate < average_price) or (
#             TRADE_TYPE == 'Short' and current_rate > average_price)
#
#
# async def trade(lots, exit=False):
#     global connection
#     await check_if_connection_is_active()
#     print("{} {} for {} volume".format(CURRENCY, TRADE_TYPE, str(lots)))
#     print("Average is {}".format(str(average_price)))
#     if exit:
#         try:
#             if TRADE_TYPE == 'Long':
#                 trade_info = await connection.create_market_sell_order(CURRENCY, lots)
#             else:
#                 trade_info = await connection.create_market_buy_order(CURRENCY, lots)
#             print(trade_info)
#             return {'status': True, 'price': None, 'quantity': lots}
#         except Exception as err:
#             print('Trade failed with error:' + str(err))
#             return {'status': False, 'price': 0, 'quantity': 0}
#
#     else:
#         current_rate = await get_current_rate()
#         if cannot_trade(current_rate):
#             print("Cannot trade since current price {} does not meet condition with average price {}".format(
#                 str(current_rate), str(average_price)))
#             return {'status': False, 'price': 0, 'quantity': 0}
#         try:
#             print("VOLUME = " + str(lots))
#             if TRADE_TYPE == 'Long':
#                 trade_info = await connection.create_market_buy_order(CURRENCY, lots)
#             else:
#                 trade_info = await connection.create_market_sell_order(CURRENCY, lots)
#             print(trade_info)
#             return {'status': True, 'price': current_rate, 'quantity': lots}
#         except Exception as err:
#             print('Trade failed with error:' + str(err))
#             return {'status': False, 'price': 0, 'quantity': 0}
#
#
# def clean_extraction_sets():
#     for current_set in execution_sets:
#         start = current_set['start']
#         end = current_set['end']
#         current_set['start'] = dt.datetime.now().replace(hour=start['hour'], minute=start['min'],
#                                                          second=start['sec'], microsecond=0)
#         current_set['end'] = dt.datetime.now().replace(hour=end['hour'], minute=end['min'],
#                                                        second=end['sec'], microsecond=0)
#         if current_set['end'] < current_set['start']:
#             current_set['end'] = current_set['end'] + dt.timedelta(days=1)
#         current_set['count'] = (
#                 (current_set['end'] - current_set['start']) / duration_between_trades_in_seconds).seconds
#
#
# async def trade_execution_sets():
#     global carry_over_from_previous_set, total_expense, total_quantity, average_price
#     for current_set in execution_sets:
#         while dt.datetime.now() < current_set['start']:
#             print(dt.datetime.now())
#             time.sleep(1)
#         if current_set['start'] <= dt.datetime.now() <= current_set['end']:
#             current_set['lots'] += carry_over_from_previous_set
#             current_set['pending'] = current_set['lots']
#             current_set['trade_lots_per_trade'] = current_set['lots'] / current_set['count']
#             for i in range(current_set['count']):
#                 try:
#                     await get_connection_to_mt4()
#                     trade_info = await trade(current_set['trade_lots_per_trade'])
#                     print(trade_info['status'])
#                     await connection.close()
#                     await account.undeploy()
#                     if trade_info['status']:
#                         trade_expense = trade_info['price'] * trade_info['quantity']
#                         total_expense += trade_expense
#                         total_quantity += trade_info['quantity']
#                         current_set['pending'] -= trade_info['quantity']
#                     await connection.close()
#                     await account.undeploy()
#                 except Exception as err:
#                     print('Exception' + str(err))
#                     await connection.close()
#                     await account.undeploy()
#                 time.sleep(duration_between_trades_in_seconds)
#             print(current_set)
#             carry_over_from_previous_set = current_set['pending']
#             average_price = total_expense / total_quantity
#         time.sleep(duration_between_execution_sets_in_seconds)
#
#
# async def second_phase():
#     global is_trade_taken, average_price, carry_over_from_previous_set
#     time.sleep(duration_before_second_phase_in_seconds)
#     await get_connection_to_mt4()
#     try:
#         trade_info = await trade(carry_over_from_previous_set / 2)
#         is_trade_taken = trade_info['status']
#         carry_over_from_previous_set = carry_over_from_previous_set / 2 if is_trade_taken else carry_over_from_previous_set
#         print(is_trade_taken)
#         await connection.close()
#         await account.undeploy()
#     except Exception as err:
#         print('Exception ' + str(err))
#         await connection.close()
#         await account.undeploy()
#
#
# async def third_phase():
#     global is_trade_taken, average_price, carry_over_from_previous_set, connection, total_quantity, total_lots, number_of_exit_trades
#     time.sleep(duration_before_third_phase_in_seconds)
#     await get_connection_to_mt4()
#     if is_trade_taken:
#         await trade(carry_over_from_previous_set)
#     else:
#         current_rate = await get_current_rate()
#         if cannot_trade(current_rate):
#             print("Exiting position {} till 20%".format(total_quantity))
#             volume_to_be_exited = total_quantity - total_lots * 0.2
#             volume_per_exit_trade = volume_to_be_exited / number_of_exit_trades
#
#             while total_quantity > total_lots * 0.2:
#                 positions = await connection.get_positions()
#                 latest_position = positions[0]
#                 latest_position_id = latest_position['id']
#                 latest_position_vol = latest_position['volume']
#                 exit_vol = min(latest_position_vol, volume_per_exit_trade)
#                 trade_info = await connection.close_position_partially(latest_position_id, exit_vol)
#                 print(trade_info)
#                 total_quantity -= volume_per_exit_trade
#                 time.sleep(duration_between_TWAP_execution_in_seconds)
#
#     await connection.close()
#     await account.undeploy()
#
#
# async def trade_smart():
#     global connection, account
#     connection, account = await get_connection_to_mt4()
#     clean_extraction_sets()
#     await trade_execution_sets()
#     await second_phase()
#     await third_phase()
#
#
# asyncio.run(trade_smart())
