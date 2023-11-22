import pandas as pd
import os
from nautilus_trader.persistence.wranglers import BarDataWrangler
from nautilus_trader.persistence.loaders import CSVBarDataLoader
from nautilus_trader.test_kit.providers import TestInstrumentProvider
from nautilus_trader.persistence.catalog import ParquetDataCatalog
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import Bar
from nautilus_trader.backtest.node import BacktestNode, BacktestVenueConfig, BacktestDataConfig, BacktestRunConfig, BacktestEngineConfig
from nautilus_trader.config.common import ImportableStrategyConfig
from decimal import Decimal

data_path = "./data"
tickers = ['AUD/CAD','AUD/JPY','AUD/NZD','CHF/JPY','EUR/GBP','EUR/USD','GBP/NZD','USD/JPY']

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
        strategy_path="nautilus_trader.examples.strategies.ema_cross:EMACross",
        config_path="nautilus_trader.examples.strategies.ema_cross:EMACrossConfig",
        config=dict(
            instrument_id=instrument.id.value,
            #bar_type=BarType.from_catalog(instrument.id.value, catalog).value,
            fast_ema_period=10,
            slow_ema_period=20,
            trade_size=Decimal(1_000_000),
        ),
    ),
]

config = BacktestRunConfig(
    engine=BacktestEngineConfig(strategies=strategies),
    data=data_configs,
    venues=venue_configs,
)

node = BacktestNode(configs=[config])

results = node.run()
results

