# This is not production grade code.  
# I published it so that I could share the code, ask for help, 
# and get feedback from the community.

import time

import pandas as pd

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.config.common import LoggingConfig
from nautilus_trader.model.currencies import USD
from nautilus_trader.model.data import BarType
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OmsType
from nautilus_trader.model.identifiers import Venue
from nautilus_trader.model.objects import Money
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.loaders import CSVBarDataLoader
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.enums import OrderSide

import os


if __name__ == "__main__":

    config = BacktestEngineConfig(
        trader_id="BACKTESTER-001",
        logging=LoggingConfig(
          log_level="ERROR",
          log_level_file="DEBUG",
          ),
    )
  
    # Build backtest engine
    engine = BacktestEngine(config=config)

    # Add a trading venue (multiple venues possible)
    SIM = Venue("SIM")
    engine.add_venue(
        venue=SIM,
        oms_type=OmsType.NETTING,  # Venue will generate position IDs
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

    # strategy

    class BuyAndHold(Strategy):
      def __init__(self) -> None:
        super().__init__() 

      def on_start(self) -> None:
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
          self.log.error(f"Could not find instrument for {self.instrument_id}")
          self.stop()
          return
     
        self.bar_type = f"{instrument.id.value}-1-DAY-LAST-EXTERNAL"
            
        self.request_instrument(self.instrument)
        self.request_bars(self.bar_type)
        self.subscribe_bars(self.bar_type)

      def on_stop(self) -> None:
        self.close_all_positions(self.instrument_id)

      def on_bar(self) -> None:
        try:
          self.order_factory.market(
            instrument_id=instrument.id.value,
            order_side=OrderSide.BUY,
            quantity=1,
          )
        except:
          self.log.warning("Did not place an order.")
      
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
