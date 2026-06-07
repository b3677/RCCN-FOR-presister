import numpy as np
from scipy import sparse


def sample_cycle_lengths(num_spins, max_cycle_length, rng):
    """Sample cycle lengths using the MATLAB initJij.m rule."""
    cycle_lengths = []
    total = 0

    while total < num_spins:
        block_size = int(np.floor(1.0 / (rng.random() ** (1.0 / 0.5))))
        while block_size > max_cycle_length:
            block_size = int(np.floor(1.0 / (rng.random() ** (1.0 / 0.5))))

        block_size = min(block_size, num_spins - total)
        cycle_lengths.append(block_size)
        total += block_size

    return np.asarray(cycle_lengths, dtype=np.int64)


def make_cycle_starts(cycle_lengths):
    starts = np.empty(len(cycle_lengths), dtype=np.int64)
    starts[0] = 0
    starts[1:] = np.cumsum(cycle_lengths[:-1])
    return starts


def choose_coupling_indices(cycle_starts, cycle_lengths, rng):
    coupling_indices = []
    coupling_cycle_ids = []

    for cycle_id, (start, length) in enumerate(zip(cycle_starts, cycle_lengths)):
        if length > 1:
            coupling_indices.append(start + rng.integers(0, length))
            coupling_cycle_ids.append(cycle_id)

    return (
        np.asarray(coupling_indices, dtype=np.int64),
        np.asarray(coupling_cycle_ids, dtype=np.int64),
    )


def build_shift_edges(cycle_starts, cycle_lengths):
    rows = []
    cols = []
    values = []

    for start, length in zip(cycle_starts, cycle_lengths):
        indices = np.arange(start, start + length)
        rows.extend(indices)
        cols.extend(np.roll(indices, -1))
        values.extend(np.ones(length))

    return rows, cols, values


def build_intercycle_edges(coupling_indices, coupling_cycle_ids, gamma, num_cycles, rng):
    rows = []
    cols = []
    values = []

    if len(coupling_indices) == 0:
        return rows, cols, values

    scale = gamma / np.sqrt(num_cycles)
    weights = rng.normal(0.0, scale, size=(len(coupling_indices), len(coupling_indices)))

    for target_pos, target in enumerate(coupling_indices):
        for source_pos, source in enumerate(coupling_indices):
            # MATLAB later overwrites within-cycle blocks with genShiftMat.
            if coupling_cycle_ids[target_pos] == coupling_cycle_ids[source_pos]:
                continue
            rows.append(target)
            cols.append(source)
            values.append(weights[target_pos, source_pos])

    return rows, cols, values


def build_rccn_network(params, rng):
    cycle_lengths = sample_cycle_lengths(
        params["num_spins"], params["max_cycle_length"], rng
    )
    cycle_starts = make_cycle_starts(cycle_lengths)
    coupling_indices, coupling_cycle_ids = choose_coupling_indices(
        cycle_starts, cycle_lengths, rng
    )

    rows, cols, values = build_shift_edges(cycle_starts, cycle_lengths)
    inter_rows, inter_cols, inter_values = build_intercycle_edges(
        coupling_indices,
        coupling_cycle_ids,
        params["gamma"],
        len(cycle_lengths),
        rng,
    )
    rows.extend(inter_rows)
    cols.extend(inter_cols)
    values.extend(inter_values)

    J = sparse.csr_matrix(
        (values, (rows, cols)),
        shape=(params["num_spins"], params["num_spins"]),
        dtype=np.float64,
    )

    return {
        "J": J,
        "cycle_starts": cycle_starts,
        "cycle_lengths": cycle_lengths,
        "coupling_indices": coupling_indices,
    }

