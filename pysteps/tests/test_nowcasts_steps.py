# -*- coding: utf-8 -*-

import pytest

from pysteps import motion, nowcasts, verification
from pysteps.tests.helpers import get_precipitation_fields

steps_arg_names = (
    "n_ens_members",
    "n_cascade_levels",
    "ar_order",
    "mask_method",
    "probmatching_method",
    "domain",
    "max_crps",
)

steps_arg_values = [
    (5, 6, 2, None, None, "spatial", 1.55),
    (5, 6, 2, "incremental", None, "spatial", 6.65),
    (5, 6, 2, "sprog", None, "spatial", 7.65),
    (5, 6, 2, "obs", None, "spatial", 7.65),
    (5, 6, 2, None, "cdf", "spatial", 0.70),
    (5, 6, 2, None, "mean", "spatial", 1.55),
    (5, 6, 2, None, "mean", "spatial", 1.55),
    (5, 6, 2, "incremental", "cdf", "spectral", 1.55),
]


@pytest.mark.parametrize(steps_arg_names, steps_arg_values)
def test_steps(
    n_ens_members,
    n_cascade_levels,
    ar_order,
    mask_method,
    probmatching_method,
    domain,
    max_crps,
):
    """Tests STEPS nowcast."""
    # inputs
    precip_input, metadata = get_precipitation_fields(
        num_prev_files=2,
        num_next_files=0,
        return_raw=False,
        metadata=True,
        upscale=2000,
    )
    precip_input = precip_input.filled()

    precip_obs = get_precipitation_fields(
        num_prev_files=0, num_next_files=3, return_raw=False, upscale=2000
    )[1:, :, :]
    precip_obs = precip_obs.filled()

    # Retrieve motion field
    pytest.importorskip("cv2")
    oflow_method = motion.get_method("LK")
    retrieved_motion = oflow_method(precip_input)

    # Run nowcast
    nowcast_method = nowcasts.get_method("steps")

    precip_forecast = nowcast_method(
        precip_input,
        retrieved_motion,
        n_timesteps=3,
        R_thr=metadata["threshold"],
        kmperpixel=2.0,
        timestep=metadata["accutime"],
        seed=42,
        n_ens_members=n_ens_members,
        n_cascade_levels=n_cascade_levels,
        ar_order=ar_order,
        mask_method=mask_method,
        probmatching_method=probmatching_method,
        domain=domain,
    )

    # result
    crps = verification.probscores.CRPS(precip_forecast[-1], precip_obs[-1])
    print(f"got CRPS={crps:.1f}, required < {max_crps:.1f}")
    assert crps < max_crps


if __name__ == "__main__":
    for n in range(len(steps_arg_values)):
        test_args = zip(steps_arg_names, steps_arg_values[n])
        test_steps(**dict((x, y) for x, y in test_args))
