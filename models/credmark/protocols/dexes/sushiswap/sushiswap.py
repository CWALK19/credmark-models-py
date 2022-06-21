from credmark.cmf.model import Model

from credmark.cmf.types import (
    Address,
    Contract,
    Token,
    Contracts,
)

from credmark.dto import (
    DTO,
    EmptyInput,
)

from models.credmark.protocols.dexes.uniswap.uniswap_v2 import (
    UniswapV2PoolMeta,
    UniswapPoolPriceInfoMeta,
)
from models.dtos.price import PoolPriceInfos


@Model.describe(slug="sushiswap.get-v2-factory",
                version="1.0",
                display_name="Sushiswap - get factory",
                description="Returns the address of Suishiswap factory contract",
                input=EmptyInput,
                output=Contract)
class SushiswapV2Factory(Model):
    SUSHISWAP_V2_FACTORY_ADDRESS = {
        1: '0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac',
    } | {
        k: '0xc35DADB65012eC5796536bD9864eD8773aBc74C4' for k in [3, 4, 5, 42]
    }

    def run(self, _) -> Contract:
        addr = self.SUSHISWAP_V2_FACTORY_ADDRESS[self.context.chain_id]
        contract = Contract(address=addr)
        return contract


@Model.describe(slug='sushiswap.get-pools',
                version='1.1',
                display_name='Sushiswap v2 Pools',
                description='The Sushiswap pools where a token is traded',
                input=Token,
                output=Contracts)
class SushiswapGetPoolsForToken(Model, UniswapV2PoolMeta):
    def run(self, input: Token) -> Contracts:
        contract = Contract(**self.context.models.sushiswap.get_v2_factory())
        return self.get_uniswap_pools(input, contract.address)


@Model.describe(slug="sushiswap.all-pools",
                version="1.1",
                display_name="Sushiswap all pairs",
                description="Returns the addresses of all pairs on Suhsiswap protocol")
class SushiswapAllPairs(Model):
    def run(self, input) -> dict:
        contract = Contract(**self.context.models.sushiswap.get_v2_factory())
        allPairsLength = contract.functions.allPairsLength().call()
        sushiswap_pairs_addresses = []

        error_count = 0
        for i in range(allPairsLength):
            try:
                pair_address = contract.functions.allPairs(i).call()
                sushiswap_pairs_addresses.append(Address(pair_address).checksum)
            except Exception as _err:
                error_count += 1

        self.logger.warning(f'There are {error_count} errors in total {allPairsLength} pools.')

        return {"result": sushiswap_pairs_addresses,
                'all_pairs_lenght': allPairsLength,
                'error_count': error_count}


class SushiSwapPool(DTO):
    token0: Token
    token1: Token


@Model.describe(slug="sushiswap.get-pool",
                version="1.0",
                display_name="Sushiswap get pool for a pair of tokens",
                description=("Returns the addresses of the pool of "
                             "both tokens on Suhsiswap protocol"),
                input=SushiSwapPool)
class SushiswapGetPair(Model):
    def run(self, input: SushiSwapPool):
        self.logger.info(f'{input=}')
        contract = Contract(**self.context.models.sushiswap.get_v2_factory())

        if input.token0.address and input.token1.address:
            token0 = input.token0.address.checksum
            token1 = input.token1.address.checksum

            pair_pool = contract.functions.getPair(token0, token1).call()
            return {'pool': pair_pool}
        else:
            return {}


@Model.describe(slug='sushiswap.get-pool-price-info',
                version='1.0',
                display_name='Sushiswap Token Pools Price ',
                description='Gather price and liquidity information from pools',
                input=Token,
                output=PoolPriceInfos)
class SushiswapGetAveragePrice(Model, UniswapPoolPriceInfoMeta):
    def run(self, input: Token) -> PoolPriceInfos:
        pools_address = self.context.run_model('sushiswap.get-pools',
                                               input,
                                               return_type=Contracts)

        return self.get_pool_price_infos(self,
                                         input,
                                         pools_address,
                                         pricer_slug='sushiswap.get-weighted-price')
