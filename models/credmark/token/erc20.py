import credmark.model
from credmark.types import Address, AddressDTO
from credmark.types.dto import DTO, DTOField

MIN_ERC20_ABI = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'


class ERC20LookupDTO(DTO):
    address: Address = DTOField(None, description='Token Address')
    symbol: str = DTOField(None, description='Token Symbol')


class TokenAmountDto(DTO):
    address: Address = DTOField(None, description='Token Address')
    amount: str = DTOField(None, description="The amount of a Token")
    scaledAmount: float = DTOField(
        None, description="The Amount of a Token, scaled by decimal Amount")


class BalanceOfInputDTO(DTO):
    token: Address
    address: Address


@credmark.model.describe(slug='erc20-totalSupply',
                         version='1.0',
                         display_name='ERC20 Total Supply',
                         description='Get the Total Supply of an ERC20',
                         input=AddressDTO,
                         output=TokenAmountDto
                         )
class TotalSupply(credmark.model.Model):

    def run(self, input: AddressDTO) -> TokenAmountDto:
        contract = self.context.contracts.load_address(input.address.checksum)
        totalSupply = contract.functions.totalSupply().call()
        decimals = contract.functions.decimals().call()
        scaledAmount = totalSupply / (10**decimals)
        return TokenAmountDto(**{"address": input.address, "amount": totalSupply, "scaledAmount": scaledAmount})


@credmark.model.describe(slug='erc20-balanceOf',
                         version='1.0',
                         display_name='ERC20 balanceOf',
                         description='Get the balance of an ERC20 Token from a wallet address',
                         input=BalanceOfInputDTO)
class BalanceOf(credmark.model.Model):

    def run(self, input: BalanceOfInputDTO) -> TokenAmountDto:
        contract = self.context.contracts.load_address(input.token)
        balanceOf = contract.functions.balanceOf(input.address.checksum).call()
        decimals = contract.functions.decimals().call()
        scaledAmount = balanceOf / (10**decimals)
        return TokenAmountDto(**{"address": input.address, "amount": balanceOf, "scaledAmount": scaledAmount})
