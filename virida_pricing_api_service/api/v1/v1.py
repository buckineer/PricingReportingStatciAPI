from fastapi import APIRouter
from .routers import pricing, forex, interest_rate, benchmark, limit, utilization, api_key, standardized_instrument, config, history, model_config, benchmark_index 
from core.models import ConditionalFactorEncoder
from core.models import ViridaPrices

router = APIRouter()


# route to apikey blacklist
router.include_router(api_key.router, prefix='/api_keys')

# route to access exchanges rates
router.include_router(forex.router, prefix="/forex")

# route to access interest rates
router.include_router(interest_rate.router, prefix="/interest_rate")

# route to access benchmarks
router.include_router(benchmark.router, prefix="/benchmark")

# route to access limits
router.include_router(limit.router, prefix="/limit")

# route to access utilization
router.include_router(utilization.router, prefix="/utilization")

# route to instrument
router.include_router(standardized_instrument.router, prefix="/standardized_instrument")

# route to config
router.include_router(config.router, prefix="/config")

# router to access model_config
router.include_router(model_config.router, prefix="/model_config")

# router to access benchmark_index
router.include_router(benchmark_index.router, prefix="/benchmark_index")

# model v7 - 23-feb-2021
# inputs7_0_0_2 = {'project': 28, 'standard': 8, 'geography': 250, 'sdg': 17}
# outputs7_0_0_2 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
# units7_0_0_2 = {'input': 800, 'hidden': [800] * 8}
# model7_0_0_2 = ViridaPrices(inputs=inputs7_0_0_2,units=units7_0_0_2,outputs=outputs7_0_0_2)
# model7_0_0_2_identifier = '800-8x800-5_v7.0.0.2_weights'
# model7_0_0_2.load_weights(f"./core/data/{model7_0_0_2_identifier}")

# model v7 - 2-mar-2021
# inputs7_0_1_3 = {'project': 28, 'standard': 8, 'geography': 250, 'sdg': 17}
# outputs7_0_1_3 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
# units7_0_1_3 = {'input': 800, 'hidden': [800] * 8}
# model7_0_1_3 = ViridaPrices(inputs=inputs7_0_1_3,units=units7_0_1_3,outputs=outputs7_0_1_3)
# model7_0_1_3_identifier = '800-8x800-5_v7.0.1.3_weights'
# model7_0_1_3.load_weights(f"./core/data/{model7_0_1_3_identifier}")

# model v7 - 6-mar-2021
#inputs7_0_2_1 = {'project': 28, 'standard': 8, 'geography': 250, 'sdg': 17}
#outputs7_0_2_1 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
#units7_0_2_1 = {'input': 800, 'hidden': [800] * 8}
#model7_0_2_1 = ViridaPrices(inputs=inputs7_0_2_1, units=units7_0_2_1, outputs=outputs7_0_2_1)
#model7_0_2_1_identifier = '800-8x800-5_v7.0.2.1_weights'
#model7_0_2_1.load_weights(f"./core/data/{model7_0_2_1_identifier}")

# model v7 - 15-mar-2021
#inputs7_0_3_0 = {'project': 28, 'standard': 8, 'geography': 250, 'sdg': 17}
#outputs7_0_3_0 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
#units7_0_3_0 = {'input': 800, 'hidden': [800] * 8}
#model7_0_3_0 = ViridaPrices(inputs=inputs7_0_3_0, units=units7_0_3_0, outputs=outputs7_0_3_0)
#model7_0_3_0_identifier = '800-8x800-5_v7.0.3.0_weights'
#model7_0_3_0.load_weights(f"./core/data/{model7_0_3_0_identifier}")

# model v7 - 13-apr-2021
#inputs7_0_4_0 = {'project': 28, 'standard': 8, 'geography': 250, 'sdg': 17}
#outputs7_0_4_0 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
#units7_0_4_0 = {'input': 800, 'hidden': [800] * 8}
#model7_0_4_0 = ViridaPrices(inputs=inputs7_0_4_0, units=units7_0_4_0, outputs=outputs7_0_4_0)
#model7_0_4_0_identifier = '800-8x800-5_v7.0.4.0_weights'
#model7_0_4_0.load_weights(f"./core/data/{model7_0_4_0_identifier}")

# model v7 - 30-apr-2021
#inputs7_0_6_1 = {'project': 23, 'standard': 8, 'geography': 250, 'sdg': 17}
#outputs7_0_6_1 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
#units7_0_6_1 = {'input': 800, 'hidden': [800] * 8}
#model7_0_6_1 = ViridaPrices(inputs=inputs7_0_6_1, units=units7_0_6_1, outputs=outputs7_0_6_1)
#model7_0_6_1_identifier = '800-8x800-5_v7.0.6.1_weights'
#model7_0_6_1.load_weights(f"./core/data/{model7_0_6_1_identifier}")

# model v7 - 24-may-2021
#inputs7_0_7_7 = {'project': 23, 'standard': 8, 'geography': 250, 'sdg': 17}
#outputs7_0_7_7 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
#units7_0_7_7 = {'input': 800, 'hidden': [800] * 8}
#model7_0_7_7 = ViridaPrices(inputs=inputs7_0_7_7, units=units7_0_7_7, outputs=outputs7_0_7_7)
#model7_0_7_7_identifier = '800-8x800-5_v7.0.7.7_weights'
#model7_0_7_7.load_weights(f"./core/data/{model7_0_7_7_identifier}")

# model v7 - 7-jun-2021
#inputs7_0_7_10 = {'project': 23, 'standard': 8, 'geography': 250, 'sdg': 17}
#outputs7_0_7_10 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
#units7_0_7_10 = {'input': 800, 'hidden': [800] * 8}
#model7_0_7_10 = ViridaPrices(inputs=inputs7_0_7_10, units=units7_0_7_10, outputs=outputs7_0_7_10)
#model7_0_7_10_identifier = '800-8x800-5_v7.0.7.10_weights'
#model7_0_7_10.load_weights(f"./core/data/{model7_0_7_10_identifier}")

# model v7 - 2-jul-2021
inputs7_0_7_11 = {'project': 23, 'standard': 8, 'geography': 250, 'sdg': 17}
outputs7_0_7_11 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
units7_0_7_11 = {'input': 800, 'hidden': [800] * 8}
model7_0_7_11 = ViridaPrices(inputs=inputs7_0_7_11, units=units7_0_7_11, outputs=outputs7_0_7_11)
model7_0_7_11_identifier = '800-8x800-5_v7.0.7.11_weights'
model7_0_7_11.load_weights(f"./core/data/{model7_0_7_11_identifier}")

# model v7 - 13-jul-2021
inputs7_0_7_12 = {'project': 23, 'standard': 8, 'geography': 250, 'sdg': 17}
outputs7_0_7_12 = {'beta': ['eua', 'co2', 'brent', 'treasury'], 'sigma': ['sigma']}
units7_0_7_12 = {'input': 800, 'hidden': [800] * 8}
model7_0_7_12 = ViridaPrices(inputs=inputs7_0_7_12, units=units7_0_7_12, outputs=outputs7_0_7_12)
model7_0_7_12_identifier = '800-8x800-5_v7.0.7.12_weights'
model7_0_7_12.load_weights(f"./core/data/{model7_0_7_12_identifier}")

router.include_router(
    pricing.router(
        config_data={
            "model": model7_0_7_12,
            "model_id": model7_0_7_12_identifier,
            "model_name": "vre_model_v7",
            "formula": 4
        }),
    prefix="/valuation/model_v7",
    tags=["pricing"]
)

router.include_router(
    history.router(
        config_data={
            "model_name": "vre",
            "model_version": "vre_v1"
        }),
    prefix="/history/vre_v1",
    tags=["pricing"]
)

router.include_router(
    history.router(
        config_data={
            "model_name": "platts",
            "model_version": "platts_v1"
        }),
    prefix="/history/platts_v1",
    tags=["pricing"]
)
