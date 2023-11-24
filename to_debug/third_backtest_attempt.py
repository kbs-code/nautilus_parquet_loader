# This is not production grade code.  
# I published it so that I could share the code, ask for help, 
# and get feedback from the community.

import time
from decimal import Decimal

import pandas as pd

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.config.common import LoggingConfig
from nautilus_trader.config.common import RiskEngineConfig
from nautilus_trader.examples.strategies.ema_cross_bracket import EMACrossBracket
from nautilus_trader.examples.strategies.ema_cross_bracket import EMACrossBracketConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.loaders import CSVBarDataLoader
import os


if __name__ == "__main__":

    config = BacktestEngineConfig(
        trader_id="BACKTESTER-001",
        logging=LoggingConfig(log_level="WARNING"),
        risk_engine=RiskEngineConfig(
            bypass=True,  # Example of bypassing pre-trade risk checks for backtests
        ),
    )

    # Build backtest engine
    engine = BacktestEngine(config=config)

    # Add a trading venue (multiple venues possible)
    SIM = Venue("SIM")
    engine.add_venue(
        venue=SIM,
        oms_type=OmsType.HEDGING,  # Venue will generate position IDs
        account_type=AccountType.MARGIN,
        base_currency=USD,  # Standard single-currency account
        starting_balances=[Money(100_000, USD)],  # Single-currency or multi-currency accounts
    )

    data_path = "./data"
    tickers = ['AUD/CAD','AUD/JPY','AUD/NZD']

    for ticker in tickers:
      instrument = TestInstrumentProvider.default_fx_ccy(ticker)
      data = os.path.join(data_path, ticker.replace('/','') + ".csv")
      df = CSVBarDataLoader.load(data)
      bar_type = BarType.from_str(ticker + ".SIM-1-DAY-LAST-EXTERNAL")
      wrangler = BarDataWrangler(
        bar_type = bar_type,
        instrument = instrument
        )
      bars = wrangler.process(df)
      engine.add_instrument(instrument)
      engine.add_data(bars)

    # Configure your strategy
    config = EMACrossBracketConfig(
        instrument_id=instrument.id.value,
        bar_type=f"{instrument.id.value}-1-DAY-LAST-EXTERNAL",
        fast_ema_period=10,
        slow_ema_period=20,
        bracket_distance_atr=3.0,
        trade_size=Decimal(1_000),
    )
    # Instantiate and add your strategy
    strategy = EMACrossBracket(config=config)
    engine.add_strategy(strategy=strategy)

    time.sleep(0.1)
    input("Press Enter to continue...")

    # Run the engine (from start to end of data)
    engine.run()

    # Optionally view reports
    with pd.option_context(
        "display.max_rows",
        100,
        "display.max_columns",
        None,
        "display.width",
        300,
    ):
        print(engine.trader.generate_account_report(SIM))
        print(engine.trader.generate_order_fills_report())
        print(engine.trader.generate_positions_report())

    # For repeated backtest runs make sure to reset the engine
    engine.reset()

    # Good practice to dispose of the object when done
    engine.dispose()
