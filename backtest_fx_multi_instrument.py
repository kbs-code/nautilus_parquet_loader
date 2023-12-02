# This is not production grade code.  
# I published it so that I could share the code, ask for help, 
# and get feedback from the community.


import pandas as pd
import os
from nautilus_trader.persistence.catalog import ParquetDataCatalog 
from nautilus_trader.model.data import Bar
from nautilus_trader.backtest.node import (
                                          BacktestNode, 
                                          BacktestVenueConfig, 
                                          BacktestDataConfig, 
                                          BacktestRunConfig, 
                                          BacktestEngineConfig
                                          )
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config.common import ImportableStrategyConfig
from strategies.BuyAndHold import BuyAndHoldConfig
from strategies.BuyAndHold import BuyAndHold
# catalog contains several tickers with bar data
CATALOG_PATH = os.getcwd() + "/catalog"
catalog = ParquetDataCatalog(CATALOG_PATH)

bars = catalog.bars()

instrument = catalog.instruments(as_nautilus=True)[0]

venue_configs = [
  BacktestVenueConfig(
    name="SIM",
    oms_type="NETTING",
    account_type="MARGIN",
    base_currency="USD",
    starting_balances=["100_000 USD"],
  ),
]

data_configs = [
  BacktestDataConfig(
    catalog_path=CATALOG_PATH,
    data_cls=Bar,
    instrument_id=instrument.id.value,
  ),
]

strategies = [
    ImportableStrategyConfig(
      strategy_path=BuyAndHold,
      config_path=BuyAndHoldConfig,
      config=dict(
        instrument_id=instrument.id.value,
        bar_type=f"{instrument.id.value}-1-DAY-LAST-EXTERNAL",
      ),
    ),
]

logging_config = LoggingConfig(
  log_level="INFO",
  log_level_file="DEBUG",
)

engine_configs = BacktestEngineConfig(
  strategies=strategies,
  logging=logging_config,
)

run_config = BacktestRunConfig(
  venues=venue_configs,
  data=data_configs,
  engine=engine_configs,
)

node = BacktestNode(configs=[run_config])

results = node.run()
results

