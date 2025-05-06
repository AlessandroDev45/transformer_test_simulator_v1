"""
Pacote de fórmulas matemáticas para o simulador de ensaios de transformadores.
Centraliza todos os cálculos matemáticos usados na aplicação.
"""

# Importa as funções principais para facilitar o acesso
from .impulse_math import (
    double_exp_func,
    rlc_solution,
    simulate_hybrid_impulse,
    calculate_k_factor_transform,
    analyze_lightning_impulse,
    analyze_switching_impulse,
    calculate_gap_chopping,
    get_resistors_and_inductor,
    parallel_resistors
)

from .transformer_math import (
    calculate_transformer_inductance,
    calculate_short_circuit_params,
    calculate_impedance_variation
)

from .thermal_math import (
    calculate_winding_temps,
    calculate_top_oil_rise,
    calculate_thermal_time_constant
)

from .losses_math import (
    calculate_empty_losses,
    calculate_load_losses
)

from .electrical_math import (
    calculate_capacitive_load,
    calculate_circuit_efficiency,
    calculate_energy_requirements,
    calculate_total_load_capacitance
)

from .utils import (
    safe_float,
    safe_int,
    find_nearest_index,
    interpolate_linear
)
