"""
Example: Agent Exploration with Trajectory Optimization in CMF

This example demonstrates how to use the trajectory optimization module
to capture, merge, and leverage agent explorations across multiple runs.

Scenario: Hyperparameter optimization for neural networks using sequential agents
with trajectory inheritance and SAW constraints.
"""

import numpy as np
from pathlib import Path
import sys

# Add cmflib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cmflib.trajectory_optimization import (
    Trajectory, Waypoint, SAWConstraint, 
    TrajectoryAcquisitionFunction, TrajectoryBayesianOptimizer,
    create_trajectory_from_points, save_trajectory, load_trajectory
)


def objective_function(x: np.ndarray) -> float:
    """
    Example objective function: Rosenbrock-like 10D function
    Agents try to minimize this function.
    """
    x = np.array(x)
    # Shifted minimum at (0.3, 0.3, ..., 0.3)
    shifted = x - 0.3
    result = sum(100 * (shifted[i+1] - shifted[i]**2)**2 + (1 - shifted[i])**2 
                 for i in range(len(x)-1))
    return result


def simulate_agent_exploration(agent_id: str, n_steps: int, 
                               initial_point: np.ndarray,
                               saw_constraint: SAWConstraint = None) -> Trajectory:
    """
    Simulate an agent exploring the search space.
    
    Args:
        agent_id: Identifier for this agent
        n_steps: Number of exploration steps
        initial_point: Starting point in search space
        saw_constraint: Optional SAW constraint to respect
    
    Returns:
        Trajectory of exploration
    """
    points = [initial_point]
    metrics = [objective_function(initial_point)]
    
    current = np.array(initial_point, dtype=float)
    
    for step in range(1, n_steps):
        # Generate candidate next point via simple random walk
        candidate = current + 0.1 * np.random.randn(len(current))
        candidate = np.clip(candidate, 0, 1)  # Keep in [0, 1]^d
        
        # Apply SAW constraint if available
        if saw_constraint and not saw_constraint.is_valid(candidate):
            # Apply penalty: move toward frontier
            penalty_factor = saw_constraint.compute_penalty(candidate)
            if penalty_factor < 0.5:
                # Try to move away from explored regions
                candidate = current + 0.05 * np.random.randn(len(current))
                candidate = np.clip(candidate, 0, 1)
        
        metric = objective_function(candidate)
        points.append(candidate.copy())
        metrics.append(metric)
        
        # 20% chance to accept worse solution (exploration)
        if metric < metrics[-2] or np.random.rand() < 0.2:
            current = candidate.copy()
    
    # Create trajectory
    trajectory = create_trajectory_from_points(
        trajectory_id=f"traj_{agent_id}_{np.random.randint(10000):04d}",
        agent_id=agent_id,
        points=points,
        metrics=metrics,
        algorithm="random_walk"
    )
    
    return trajectory


def main():
    """Run example with multiple agents and trajectory inheritance"""
    
    print("=" * 80)
    print("CMF Trajectory Optimization Example")
    print("=" * 80)
    
    # Configuration
    n_agents = 3
    n_steps_per_agent = 100
    dimensionality = 10
    exclusion_radius = 0.15
    
    # Initialize SAW constraint and acquisition function
    saw_constraint = SAWConstraint(
        exclusion_radius=exclusion_radius,
        dimensionality=dimensionality
    )
    acq_fn = TrajectoryAcquisitionFunction(
        w_exploit=0.5,
        w_explore=0.3,
        w_coherence=0.2
    )
    optimizer = TrajectoryBayesianOptimizer(acq_fn)
    
    # Storage for trajectories
    all_trajectories = []
    pruned_trajectories = []
    
    print(f"\nExperiment Configuration:")
    print(f"  Agents: {n_agents}")
    print(f"  Steps per agent: {n_steps_per_agent}")
    print(f"  Dimensionality: {dimensionality}")
    print(f"  SAW exclusion radius: {exclusion_radius}")
    print()
    
    # Simulate agents
    for agent_num in range(1, n_agents + 1):
        print(f"\n{'='*80}")
        print(f"AGENT {agent_num}")
        print(f"{'='*80}")
        
        # Initialize starting point
        if agent_num == 1:
            # Agent 1 starts randomly
            start_point = np.random.rand(dimensionality)
            print(f"Agent 1: Random initialization")
        else:
            # Later agents start from best point of previous agent
            best_wp = all_trajectories[-1].best_waypoint()
            if best_wp is not None:
                start_point = best_wp.coordinates + 0.05 * np.random.randn(dimensionality)
                start_point = np.clip(start_point, 0, 1)
                print(f"Agent {agent_num}: Starting from Agent {agent_num-1}'s best point")
                print(f"  Previous best metric: {best_wp.metric_value:.6f}")
        
        # Simulate exploration
        trajectory = simulate_agent_exploration(
            agent_id=f"agent_{agent_num}",
            n_steps=n_steps_per_agent,
            initial_point=start_point,
            saw_constraint=saw_constraint if agent_num > 1 else None
        )
        
        all_trajectories.append(trajectory)
        
        # Evaluate trajectory
        best_metric = trajectory.best_metric()
        path_length = trajectory.get_path_length()
        acquisition_score = acq_fn.evaluate(trajectory)
        
        print(f"\nExploration Results:")
        print(f"  Best metric found: {best_metric:.6f}")
        print(f"  Path length: {path_length:.6f}")
        print(f"  Waypoints: {len(trajectory.waypoints)}")
        print(f"  Acquisition score: {acquisition_score:.3f}")
        
        # Add waypoints to SAW constraint
        saw_constraint.add_trajectory(trajectory)
        print(f"  SAW regions explored: {len(saw_constraint.explored_points)}")
        
        # Merge with previous trajectories
        if agent_num > 1:
            print(f"\nMerging with previous trajectories...")
            merged = saw_constraint.merge_trajectories(
                all_trajectories,
                merge_strategy='best_per_region'
            )
            print(f"  Merged waypoints: {len(merged.waypoints)}")
            print(f"  Merged best metric: {merged.best_metric():.6f}")
            
            # Select optimal trajectories
            candidates = all_trajectories
            selected = optimizer.select_optimal_trajectories(
                candidates=candidates,
                threshold_quantile=0.33
            )
            pruned_trajectories = selected
            print(f"  Pruned to {len(pruned_trajectories)} trajectories")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total trajectories: {len(all_trajectories)}")
    print(f"Pruned trajectories (for inheritance): {len(pruned_trajectories)}")
    
    metrics_over_time = [t.best_metric() for t in all_trajectories]
    print(f"\nBest metric per agent:")
    for i, metric in enumerate(metrics_over_time, 1):
        improvement = ""
        if i > 1:
            prev_metric = metrics_over_time[i-2]
            improvement_pct = ((prev_metric - metric) / prev_metric) * 100 if prev_metric != 0 else 0
            improvement = f" (improvement: {improvement_pct:+.1f}%)"
        print(f"  Agent {i}: {metric:.6f}{improvement}")
    
    # Save trajectories
    print(f"\nSaving trajectories...")
    output_dir = Path(__file__).parent / "trajectory_output"
    output_dir.mkdir(exist_ok=True)
    
    for i, traj in enumerate(all_trajectories, 1):
        filepath = output_dir / f"trajectory_agent_{i}.json"
        save_trajectory(traj, filepath)
    
    print(f"Saved {len(all_trajectories)} trajectories to {output_dir}")
    
    # Load and verify
    print(f"\nVerifying saved trajectories...")
    loaded_traj = load_trajectory(output_dir / "trajectory_agent_1.json")
    print(f"Loaded trajectory: {loaded_traj.trajectory_id}")
    print(f"  Waypoints: {len(loaded_traj.waypoints)}")
    print(f"  Best metric: {loaded_traj.best_metric():.6f}")
    
    print("\n" + "="*80)
    print("Example completed successfully!")
    print("="*80)


if __name__ == "__main__":
    np.random.seed(42)  # Reproducibility
    main()

