import os
import asyncio
import time

from metaapi_cloud_sdk import MetaApi
from metaapi_cloud_sdk.clients.metaApi.tradeException import TradeException
from datetime import datetime, timedelta

# Note: for information on how to use this example code please read https://metaapi.cloud/docs/client/usingCodeExamples

token = os.getenv(
    'TOKEN') or 'eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJiOWY5MjcxMjE0ZjMyMDM1MDk1OWU5MGJiYzJhZjI3OSIsInBlcm1pc3Npb25zIjpbXSwidG9rZW5JZCI6IjIwMjEwMjEzIiwiaW1wZXJzb25hdGVkIjpmYWxzZSwicmVhbFVzZXJJZCI6ImI5ZjkyNzEyMTRmMzIwMzUwOTU5ZTkwYmJjMmFmMjc5IiwiaWF0IjoxNjgzNzY4NjQ0fQ.XXWH16iPzCOAVv90s8IG65ttMcPp-8stQpD1kjWtp-tpJRK1b9OqXe3cr__nKpVNmWCObuti5fFA01W_reZrj79mATZIYAT063Ec1aQHY-2l0r8m6tPNVQPwUHWgk-pJbbcejm6yJ380rhvTSQ90-pj0WlYVxcW-GBWzM-TGRJbj6bBQWPpiTMwe7Tpapvo9MClM-VZCyaWs6S-KyzaEbeNo1gPVFpd7MXGXa1po2TOQiDsDIN-9RA3hYSOGjcJh5OPiFOvax-ZxS0g15lO0ozMzgNTWlnaac1nhD0dN4QYkt6AVZ5CytMjNnh1ZNYoEfrfJfcDZbp3gMnnHxrnW4jtXgn8rvnGyFQIBJ1DMJU-LympyXN3raU4_-0xim-FNgsxnfP_0G5kUugwV0ixNapu_n4fYx5Lita1njRqYYzOQTrIWCmhcvUQ6LQurkFDCKkkUrKg4OjNzu4FypuRo98-i3FkyZLII4y5rpmSWNigU0rH-37LDx4GZw5YHebPlaxVta0X-VE7DdqvWlaO5sHibinGt_FlsqfGUB_qSobuYu1WOX49qHCIARNXIHRx9RqIQT4Sv4t7S51eDWl_RIr-aD5B21kB_snW6xsnLIdfp1aRg862XOF8Hsvr8peckoBWPfoKB7FrGK24jOorsDf2MmZQyqx6Dz_xdmTU4Kcg'
accountId = os.getenv('ACCOUNT_ID') or 'e5985df9-e74a-45d6-86b0-2a56902b2e01'


async def test_meta_api_synchronization():
    api = MetaApi(token)
    try:
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
        positions = await connection.get_positions()
        print('positions:', await connection.get_positions())
        # print(await connection.get_position('1234567'))
        print('open orders:', await connection.get_orders())
        await connection.create_market_buy_order('GBPUSD', 10)
        await connection.create_market_buy_order('GBPUSD', 10)
        await connection.create_market_buy_order('GBPUSD', 10)
        await connection.create_market_buy_order('GBPUSD', 10)
        await connection.create_market_buy_order('GBPUSD', 10)
        await connection.create_market_buy_order('GBPUSD', 10)

        await connection.create_market_sell_order('USDJPY', 10)
        await connection.create_market_sell_order('USDJPY', 10)
        await connection.create_market_sell_order('USDJPY', 10)
        await connection.create_market_sell_order('USDJPY', 10)
        await connection.create_market_sell_order('USDJPY', 10)
        await connection.create_market_sell_order('USDJPY', 10)
        # # print(await connection.get_order('1234567'))
        # print('history orders by ticket:', await connection.get_history_orders_by_ticket('1234567'))
        # print('history orders by position:', await connection.get_history_orders_by_position('1234567'))
        # print('history orders (~last 3 months):',
        #       await connection.get_history_orders_by_time_range(datetime.utcnow() - timedelta(days=90),
        #                                                         datetime.utcnow()))
        # print('history deals by ticket:', await connection.get_deals_by_ticket('1234567'))
        # print('history deals by position:', await connection.get_deals_by_position('1234567'))
        # print('history deals (~last 3 months):',
        #       await connection.get_deals_by_time_range(datetime.utcnow() - timedelta(days=90), datetime.utcnow()))
        # print('server time', await connection.get_server_time())

        # calculate margin required for trade
        # print('margin required for trade', await connection.calculate_margin({
        #     'symbol': 'GBPUSD',
        #     'type': 'ORDER_TYPE_BUY',
        #     'volume': 0.1,
        #     'openPrice': 1.1
        # }))
        #
        # # trade
        # print('Submitting pending order')
        # total_quantity = 100
        # total_lots = 47.4
        # volume_to_be_exited = total_quantity - total_lots * 0.2
        # volume_per_exit_trade = volume_to_be_exited / 30
        # while total_quantity > total_lots * 0.2:
        #     positions = await connection.get_positions()
        #     latest_position = positions[0]
        #     latest_position_id = latest_position['id']
        #     latest_position_vol = latest_position['volume']
        #     exit_vol = min(latest_position_vol, volume_per_exit_trade)
        #     await connection.close_position_partially(latest_position_id, exit_vol)
        #     total_quantity -= volume_per_exit_trade
        #     time.sleep(4)
        # try:
        #     result = await connection.close_position(positions[0]['id'])
        #     print('Trade successful, result code is ' + result['stringCode'])
        # except Exception as err:
        #     print('Trade failed with error:')
        #     print(api.format_error(err))
        trade_info = await connection.create_market_buy_order("GBPUSD", 100)
        if initial_state not in deployed_states:
            # undeploy account if it was undeployed
            print('Undeploying account')
            await connection.close()
            await account.undeploy()

    except Exception as err:
        print(api.format_error(err))
    exit()


asyncio.run(test_meta_api_synchronization())
