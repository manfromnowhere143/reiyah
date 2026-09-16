"""Finite deletion factorization, version 0.1.0.

The union of both role graphs determines connected components. Deletion cannot
create an edge between them. Components with equal role membership cancel for
every deletion. Isolated references are irrelevant under an *at most* budget.
The global budget still couples all remaining components and anchors.
"""
from dataclasses import dataclass
from .contract import ROLES, graph

VERSION = '0.1.0'
MAX_LOCAL_STATES = 16384
MAX_MATCH_WORK = 2_000_000
MAX_COMBINE_WORK = 2_000_000


@dataclass(frozen=True)
class Component:
    anchor: str
    objects: frozenset
    output_a: frozenset
    output_b: frozenset
    edges: frozenset
    free: tuple

    @property
    def cancels(self):
        return self.output_a == self.output_b


@dataclass(frozen=True)
class World:
    bits: tuple
    budget: int
    components: tuple
    methods: tuple


@dataclass(frozen=True)
class Plan:
    worlds: tuple
    local_states: int
    matching_work: int
    combine_work: int
    limit: str | None


def partition(anchor, env, required, free):
    """Derive a deterministic partition from current input, never from a proof."""
    _, edges = graph(anchor, env, required)
    adjacent = {}
    for d, o in edges:
        left, right = ('d', d), ('o', o)
        adjacent.setdefault(left, set()).add(right)
        adjacent.setdefault(right, set()).add(left)
    aa, bb = ({d['id'] for d in anchor[r]['value']} for r in ROLES)
    unseen = set(adjacent)
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        vertices, pending = {start}, [start]
        while pending:
            for other in sorted(adjacent[pending.pop()]):
                if other not in vertices:
                    vertices.add(other)
                    unseen.remove(other)
                    pending.append(other)
        objects = frozenset(v for side, v in vertices if side == 'o')
        detections = {v for side, v in vertices if side == 'd'}
        result.append(Component(anchor['id'], objects, frozenset(aa & detections),
                                frozenset(bb & detections),
                                frozenset((d, o) for d, o in edges if o in objects),
                                tuple(sorted(o for o in objects if (anchor['id'], o) in free))))
    return tuple(result)


def equivalent_free_groups(component):
    """Objects with the same current neighbors are exchangeable for matching.

    Only free objects are grouped. Confirmed objects stay fixed; required
    absences were removed before partitioning. Every group permutation preserves
    both role graphs and deletion cardinality, within this particular world.
    """
    groups = {}
    for obj in component.free:
        neighborhood = tuple(sorted(d for d, o in component.edges if o == obj))
        groups.setdefault(neighborhood, []).append(obj)
    return tuple(tuple(objects) for _, objects in sorted(groups.items()))


def variants(component, budget):
    groups = equivalent_free_groups(component)

    def choose(index, remaining, deleted):
        if index == len(groups):
            yield tuple(sorted(deleted))
            return
        group = groups[index]
        for count in range(min(len(group), remaining) + 1):
            yield from choose(index + 1, remaining - count, deleted + group[:count])

    yield from choose(0, budget, ())


def state_count(component, budget, cap):
    # Count representative vectors, not all distinct labeled subsets. Partial
    # counts cannot decrease: every later group permits zero more deletions.
    counts = [1]
    for group in equivalent_free_groups(component):
        following = [0] * (min(len(counts) - 1 + len(group), budget) + 1)
        for used, ways in enumerate(counts):
            for count in range(min(len(group), budget - used) + 1):
                following[used + count] += ways
        counts = following
        if sum(counts) > cap:
            return sum(counts)
    return sum(counts)


def make_plan(case, domains):
    """Bound total local enumeration and budget convolution before solving.

    Reserve one matching pair for each unequal component before spending work
    on enumeration. Components that cannot fit retain a conservative bound.
    Limits are screening units, not wall time or a complexity theorem. Base
    world/graph activation is bounded separately by audit.unavailable.
    """
    states = work = combine = 0
    prepared = []
    for bits, env, (required, free, budget) in sorted(domains, key=lambda row: row[0]):
        free_set = set(free)
        components = tuple(c for a in case['anchors'] for c in partition(a, env, required, free_set))
        prepared.append((bits, budget, components))
        states += sum(not c.cancels for c in components)
        work += sum(matching_unit(c) for c in components if not c.cancels)
    if states > MAX_LOCAL_STATES or work > MAX_MATCH_WORK:
        return Plan((), states, work, combine, 'local_states' if states > MAX_LOCAL_STATES else 'matching_work')
    worlds = []
    for bits, budget, components in prepared:
        total_free = sum(len(c.free) for c in components if not c.cancels)
        prefix = 0
        methods = []
        for c in components:
            if c.cancels:
                methods.append('equal_outputs')
                continue
            local = state_count(c, budget, MAX_LOCAL_STATES - states + 1)
            reason = ('local_states' if states + local - 1 > MAX_LOCAL_STATES else
                      'matching_work' if work + (local - 1) * matching_unit(c) > MAX_MATCH_WORK else None)
            methods.append('bounded_' + reason if reason else 'enumerated')
            if reason is None:
                states += local - 1
                work += (local - 1) * matching_unit(c)
            # An unbounded remaining budget separates into local extrema.
            if budget < total_free:
                combine += (min(prefix, budget) + 1) * (min(len(c.free), budget) + 1)
            else:
                combine += min(len(c.free), budget) + 1
            if combine > MAX_COMBINE_WORK:
                return Plan((), states, work, combine, 'combine_work')
            prefix += len(c.free)
        worlds.append(World(tuple(bits), budget, components, tuple(methods)))
    return Plan(tuple(worlds), states, work, combine, None)


def matching_unit(component):
    return sum(2 * (len(left) + 1) * (len(component.objects) +
               sum(d in left for d, _ in component.edges) + 1)
               for left in (component.output_a, component.output_b))
