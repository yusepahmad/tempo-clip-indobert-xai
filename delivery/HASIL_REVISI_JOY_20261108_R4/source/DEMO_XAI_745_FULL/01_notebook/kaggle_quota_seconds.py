"""Read full timedelta durations; SDK to_dict omits days in this version."""
from datetime import datetime,timezone
import json
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.kernels.types.kernels_api_service import ApiGetAcceleratorQuotaStatisticsRequest

api=KaggleApi()
api.authenticate()
with api.build_kaggle_client() as client:
    response=client.kernels.kernels_api_client.get_accelerator_quota_statistics(
        ApiGetAcceleratorQuotaStatisticsRequest())
    quota=response.gpu_quota
    assert quota is not None
    used=quota.time_used.total_seconds()
    reserved=quota.time_reserved.total_seconds()
    allowed=quota.total_time_allowed.total_seconds()
    assert min(used,reserved,allowed)>=0
    print(json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),
        'refresh_at':str(response.quota_refresh_time),'used_seconds':used,
        'reserved_seconds':reserved,'allowed_seconds':allowed,
        'available_seconds':allowed-used-reserved,'allowed_hours':allowed/3600,
        'available_hours':(allowed-used-reserved)/3600,
        'duration_conversion':'datetime.timedelta.total_seconds includes days'},indent=2))
