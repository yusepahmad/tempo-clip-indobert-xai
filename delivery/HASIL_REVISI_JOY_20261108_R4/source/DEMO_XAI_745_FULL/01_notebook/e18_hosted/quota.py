"""Read official AI quota without exposing credentials; execute using Kaggle CLI venv."""
import json
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.models.types.model_proxy_api_service import ApiGetModelProxyQuotasRequest

api = KaggleApi()
api.authenticate()
with api.build_kaggle_client() as client:
    result = client.models.model_proxy_api_client.get_model_proxy_quotas(ApiGetModelProxyQuotasRequest())
    print(json.dumps([
        dict(period=str(b.refill_period), used=b.quota_used, total=b.total_quota_allowed,
             remaining=b.total_quota_allowed - b.quota_used, refill_at=str(b.refill_time))
        for b in result.quota_balances
    ]))
