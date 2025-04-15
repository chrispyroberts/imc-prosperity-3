import random
import numpy as np

containers = [
    (10, 1),
    (80, 6),
    (37, 3),
    (31, 2),
    (17, 1),
    (90, 10),
    (50, 4),
    (20, 2),
    (73, 4),
    (89, 8)
]

fee = 50000
base = 10000
participants = 1000

def simulate_distribution(power_bias, runs): # simulating a distribution based on payout from default inhabitants
    total_counts = [0] * len(containers)

    for _ in range(runs):
        scores = [(mult / inh)**power_bias for mult, inh in containers]
        total = sum(scores)
        weights = [s / total for s in scores]
        selections = random.choices(range(len(containers)), weights=weights, k=participants)
        for i in range(len(containers)):
            total_counts[i] += selections.count(i)
    return [c / runs for c in total_counts]

def approximate_nash(iterations): # chatgpt's work, approximating nash equillibrium
    n_containers = len(containers)
    prob_dist = np.array([1/n_containers] * n_containers)
    participants = 1000
    lr = 0.05  # learning rate for updates

    for step in range(iterations):
        counts = prob_dist * participants
        values = []
        for i, (mult, initial_inh) in enumerate(containers):
            open_fraction = counts[i] / participants
            denom = initial_inh + open_fraction * 100
            ev = (mult * base) / denom
            values.append(ev)

        values = np.array(values)
        best_indices = values.argsort()[::-1][:2]
        new_prob = np.zeros(n_containers)
        new_prob[best_indices] = 0.5  # 50% chance for each of top 2

        # update distribution
        prob_dist = (1 - lr) * prob_dist + lr * new_prob
    
    return prob_dist

equillibrium_dist = approximate_nash(iterations=10000)

for i in range(len(containers)):
    print(f"Container: {containers[i][0]} | Probability: {equillibrium_dist[i] * 100:.2f}")

print()

weights = [mult / initial_inh for (mult, initial_inh) in containers]
total_weight = sum(weights)
probabilities = [w / total_weight for w in weights]

total_counts = [0] * len(containers)
N_simulations = 100

# monte carlo
for _ in range(N_simulations):
    selections = random.choices(range(len(containers)), weights=weights, k=participants)
    for i in range(len(containers)):
        total_counts[i] += selections.count(i)

# counts = simulate_distribution(power_bias=2, runs=100)
counts = approximate_nash(iterations=100)

expected_values = []
total_opens_all = sum(counts)

for i, (mult, initial_inhabitants) in enumerate(containers):
    total_picked = counts[i]
    open_fraction = total_picked / total_opens_all
    denominator = initial_inhabitants + open_fraction * 100
    ev = (mult * base) / denominator
    expected_values.append((ev, mult, initial_inhabitants, open_fraction, i))

sorted_evs = sorted(expected_values, reverse=True, key=lambda x: x[0])
total_percentage = 0

print(f"{'ID':<3} | {'EV':>10} | {'Multiplier':>10} | {'Inhabitants':>12} | {'Chosen %':>10}")
print("-" * 60)
for ev, mult, initial_inhabitants, percentage, index in sorted_evs:
    print(f"{index:<3} | {ev:>10.2f} | {mult:>10} | {initial_inhabitants:>12} | {percentage * 100:>9.2f}%")
    total_percentage += percentage

# picking the best strategy under the distribution
best_strategy = None
strategy_scores = []

for i in range(len(sorted_evs)):
    ev1, _, _, _, idx1 = sorted_evs[i]
    strategy_scores.append((ev1, [idx1]))

    for j in range(i + 1, len(sorted_evs)):
        if (i == j): continue

        ev2, _, _, _, idx2 = sorted_evs[j]
        total_value = ev1 + ev2 - fee
        strategy_scores.append((total_value, [idx1, idx2]))

strategy_scores.sort(reverse=True, key=lambda x: x[0])
best_value, best_ids = strategy_scores[0]

# since we are in a nash equillibrium, there should be no action where we can exploit
# for some reason, there is a strategy (picking container with multiplier 89) gives higest payout
# this probably means that the equillibrium is not stable, but i don't think it's a horrible guess

print("\nBest strategy:")
if len(best_ids) == 1:
    print(f"Open container {best_ids[0]} only | Net Value: {best_value:.2f}")
else:
    print(f"Open containers {best_ids[0]} and {best_ids[1]} | Net Value after fee: {best_value:.2f}")
