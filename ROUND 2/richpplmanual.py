import numpy as np
import random
from scipy.optimize import minimize

# Container data: (multiplier, initial_inhabitants)
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

BASE_REWARD = 10000
FEE = 50000
PARTICIPANTS = 1000

def simulate_nash_equilibrium(iterations=1000, learning_rate=0.01):
    """Find Nash equilibrium distribution using replicator dynamics"""
    n_containers = len(containers)
    
    # Initialize with uniform distribution
    distribution = np.ones(n_containers) / n_containers
    
    for _ in range(iterations):
        # Calculate expected payoff for each container under current distribution
        expected_payoffs = np.zeros(n_containers)
        
        for i, (mult, init_inhab) in enumerate(containers):
            # Calculate how many participants would choose this container
            container_participants = distribution[i] * PARTICIPANTS
            # Calculate reward
            payoff = (mult * BASE_REWARD) / (init_inhab + container_participants)
            expected_payoffs[i] = payoff
        
        # Average payoff across all strategies
        avg_payoff = np.sum(distribution * expected_payoffs)
        
        # Update distribution using replicator dynamics
        # Strategies with above-average payoff grow, below-average shrink
        new_distribution = distribution * (1 - learning_rate + learning_rate * expected_payoffs / avg_payoff)
        # Normalize to ensure it remains a probability distribution
        new_distribution = new_distribution / np.sum(new_distribution)
        
        # Check for convergence
        if np.max(np.abs(new_distribution - distribution)) < 1e-6:
            break
            
        distribution = new_distribution
    
    return distribution

def get_expected_values(distribution):
    """Calculate expected values for each container given a population distribution"""
    expected_values = []
    
    for i, (mult, init_inhab) in enumerate(containers):
        # Calculate how many participants would choose this container
        container_participants = distribution[i] * PARTICIPANTS
        # Calculate reward
        ev = (mult * BASE_REWARD) / (init_inhab + container_participants)
        expected_values.append((ev, mult, init_inhab, distribution[i], i))
    
    return sorted(expected_values, reverse=True, key=lambda x: x[0])

def best_strategy(expected_values):
    """Find the best strategy (one or two containers) given the expected values"""
    strategies = []
    
    # Single container strategies
    for i, (ev, _, _, _, idx) in enumerate(expected_values):
        strategies.append((ev, [idx]))
    
    # Two container strategies (accounting for fee)
    for i in range(len(expected_values)):
        ev1, _, _, _, idx1 = expected_values[i]
        for j in range(i+1, len(expected_values)):
            ev2, _, _, _, idx2 = expected_values[j]
            total_value = ev1 + ev2 - FEE
            strategies.append((total_value, [idx1, idx2]))
    
    return sorted(strategies, reverse=True, key=lambda x: x[0])[0]

# Calculate Nash equilibrium distribution
print("Calculating Nash equilibrium distribution...")
nash_distribution = simulate_nash_equilibrium(iterations=2000)

print("\nNash Equilibrium Distribution:")
print(f"{'ID':<3} | {'Container':>10} | {'Distribution %':>15}")
print("-" * 40)
for i, ((mult, inhab), prob) in enumerate(zip(containers, nash_distribution)):
    print(f"{i:<3} | {f'({mult},{inhab})':>10} | {prob*100:>14.2f}%")

# Calculate expected values
print("\nExpected Values Under Nash Equilibrium:")
evs = get_expected_values(nash_distribution)
print(f"{'ID':<3} | {'EV':>10} | {'Multiplier':>10} | {'Inhabitants':>12} | {'Chosen %':>10}")
print("-" * 60)
for ev, mult, initial_inhabitants, percentage, index in evs:
    print(f"{index:<3} | {ev:>10.2f} | {mult:>10} | {initial_inhabitants:>12} | {percentage * 100:>9.2f}%")

# Find best strategy
best_value, best_ids = best_strategy(evs)
print("\nBest Strategy:")
if len(best_ids) == 1:
    container_idx = best_ids[0]
    mult, inhab = containers[container_idx]
    print(f"Open container {container_idx} only (multiplier: {mult}, inhabitants: {inhab})")
    print(f"Expected value: {best_value:.2f} SeaShells")
else:
    container1_idx, container2_idx = best_ids
    mult1, inhab1 = containers[container1_idx]
    mult2, inhab2 = containers[container2_idx]
    print(f"Open containers {container1_idx} (multiplier: {mult1}, inhabitants: {inhab1}) and")
    print(f"               {container2_idx} (multiplier: {mult2}, inhabitants: {inhab2})")
    print(f"Expected value after fee: {best_value:.2f} SeaShells")

# Verify our strategy against simulations
print("\nVerifying strategy with simulations...")

def simulate_game(strategy, population_distribution, num_trials=10000):
    """Simulate the game with our strategy against a population following the given distribution"""
    total_reward = 0
    
    for _ in range(num_trials):
        # Generate population choices
        population_choices = np.random.choice(
            len(containers), 
            size=PARTICIPANTS, 
            p=population_distribution
        )
        
        # Count participants per container
        container_counts = np.bincount(population_choices, minlength=len(containers))
        
        # Calculate our reward
        reward = 0
        for container_idx in strategy:
            mult, init_inhab = containers[container_idx]
            # We count ourselves in the participant count
            total_participants = container_counts[container_idx] + 1
            container_reward = (mult * BASE_REWARD) / (init_inhab + total_participants)
            reward += container_reward
        
        # Subtract fee if we chose two containers
        if len(strategy) == 2:
            reward -= FEE
            
        total_reward += reward
    
    return total_reward / num_trials

best_strategy_reward = simulate_game(best_ids, nash_distribution)
print(f"Average reward from best strategy: {best_strategy_reward:.2f} SeaShells")

# Compare with other top strategies
print("\nComparing top strategies:")
top_strategies = sorted([(simulate_game([i], nash_distribution), [i]) for i in range(len(containers))], 
                        reverse=True, key=lambda x: x[0])

print(f"{'Rank':<5} | {'Strategy':>20} | {'Expected Reward':>15}")
print("-" * 50)
for rank, (reward, container_ids) in enumerate(top_strategies[:5], 1):
    container_desc = ", ".join([f"{i}({containers[i][0]},{containers[i][1]})" for i in container_ids])
    print(f"{rank:<5} | {container_desc:>20} | {reward:>15.2f}")

# Check if any two-container strategy beats our best single container
best_two_container = None
best_two_reward = 0

for i in range(len(containers)):
    for j in range(i+1, len(containers)):
        reward = simulate_game([i, j], nash_distribution)
        if reward > best_two_reward:
            best_two_reward = reward
            best_two_container = [i, j]

print(f"\nBest two-container strategy: {best_two_container}")
print(f"Expected reward: {best_two_reward:.2f} SeaShells")

if best_two_reward > top_strategies[0][0]:
    print("A two-container strategy is better than the best single container!")
else:
    print("The best strategy is to select a single container.")

# FINAL RECOMMENDATION
print("\n=== FINAL RECOMMENDATION ===")
if best_two_reward > top_strategies[0][0]:
    container1_idx, container2_idx = best_two_container
    mult1, inhab1 = containers[container1_idx]
    mult2, inhab2 = containers[container2_idx]
    print(f"Choose containers {container1_idx} (multiplier: {mult1}, inhabitants: {inhab1}) and")
    print(f"                 {container2_idx} (multiplier: {mult2}, inhabitants: {inhab2})")
    print(f"Expected value after fee: {best_two_reward:.2f} SeaShells")
else:
    best_container_idx = top_strategies[0][1][0]
    mult, inhab = containers[best_container_idx]
    print(f"Choose container {best_container_idx} (multiplier: {mult}, inhabitants: {inhab})")
    print(f"Expected value: {top_strategies[0][0]:.2f} SeaShells")