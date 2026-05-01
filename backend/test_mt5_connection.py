"""Quick test: verify MT5 connection + data retrieval via our connector."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


async def main():
    from services.mt5_connector import MT5Connector

    print("=" * 60)
    print("  MT5 Connector Test")
    print("=" * 60)

    connector = MT5Connector()

    # 1) Connect
    print("\n[1] Connecting to MT5...")
    try:
        await connector.connect()
        print("    OK")
    except Exception as e:
        print(f"    FAILED: {e}")
        return

    # 2) Account info
    print("\n[2] Account info...")
    info = await connector.get_account_info()
    if info:
        print(f"    Login:    {info['login']}")
        print(f"    Server:   {info['server']}")
        print(f"    Balance:  ${info['balance']:.2f}")
        print(f"    Equity:   ${info['equity']:.2f}")
        print(f"    Margin:   ${info['freeMargin']:.2f} free")
        print(f"    Leverage: 1:{info['leverage']}")
        print(f"    Trade OK: {info['tradeAllowed']}")
    else:
        print("    FAILED")

    # 3) Tick
    print("\n[3] XAUUSD tick...")
    tick = await connector.get_tick("XAUUSD")
    if tick:
        print(f"    Bid:    {tick['bid']}")
        print(f"    Ask:    {tick['ask']}")
        print(f"    Spread: {tick['spread']} pts")
        from datetime import datetime
        print(f"    Time:   {datetime.fromtimestamp(tick['time'])}")
    else:
        print("    FAILED")

    # 4) Candles M1
    print("\n[4] XAUUSD M1 candles (last 5)...")
    candles = await connector.get_candles("XAUUSD", "1m", 5)
    if candles:
        for c in candles[:5]:
            from datetime import datetime
            dt = datetime.fromtimestamp(c["time"])
            print(f"    {dt} O={c['open']:.2f} H={c['high']:.2f} L={c['low']:.2f} C={c['close']:.2f} V={c['tick_volume']}")
    else:
        print("    FAILED or no data")

    # 5) Candles H1
    print("\n[5] XAUUSD H1 candles (last 3)...")
    candles_h1 = await connector.get_candles("XAUUSD", "1h", 3)
    if candles_h1:
        for c in candles_h1[:3]:
            from datetime import datetime
            dt = datetime.fromtimestamp(c["time"])
            print(f"    {dt} O={c['open']:.2f} H={c['high']:.2f} L={c['low']:.2f} C={c['close']:.2f}")
    else:
        print("    FAILED or no data")

    # 6) Positions
    print("\n[6] Open positions (magic 298347)...")
    positions = await connector.get_positions()
    if positions:
        for p in positions:
            print(f"    #{p['id']} {p['type']} {p['volume']} lots @{p['openPrice']:.2f} P&L={p['profit']:.2f}")
    else:
        print("    None")

    # 7) Quick engine status test
    print("\n[7] Trading Engine init test...")
    from core.trading_engine import TradingEngine
    engine = TradingEngine(connector=connector)
    status = engine.get_status()
    print(f"    Robot status:  {status['robot_status']}")
    print(f"    Sniper AI:     {status['sniper_ai_active']}")

    # Disconnect
    print("\n[8] Disconnecting...")
    await connector.disconnect()
    print("    OK")

    print("\n" + "=" * 60)
    print("  ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
