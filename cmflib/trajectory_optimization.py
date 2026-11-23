"""
Trajectory Optimization Module for CMF

This module provides abstractions and utilities for capturing, merging, and optimizing
agent exploration trajectories within the Common Metadata Framework.

Classes:
    Waypoint: Represents a single point in an exploration trajectory
    Trajectory: Represents a complete exploration path
    TrajectoryLogger: Logs trajectories to CMF metadata store
    SAWConstraint: Manages self-avoiding walk constraints
    TrajectoryAcquisitionFunction: Evaluates trajectories via multi-objective acquisition
    TrajectoryBayesianOptimizer: Performs trajectory-level Bayesian optimization
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Tuple, Callable
from enum import Enum
import json
import logging
import numpy as np
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class TrajectoryStatus(Enum):
    """Enumeration of possible trajectory statuses"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PRUNED = "pruned"
    INHERITED = "inherited"
    MERGED = "merged"


@dataclass
class Waypoint:
    """
    Represents a single point on an exploration trajectory.
    
    Attributes:
        coordinates: n-dimensional coordinates in search space (numpy array)
        metric_value: Objective function value at this waypoint
        step_number: Order in the trajectory sequence
        cost_from_previous: Cost/distance to reach this waypoint from previous
        timestamp: Unix timestamp when waypoint was recorded
        additional_metrics: Dict of domain-specific metrics at this point
    """
    coordinates: np.ndarray
    metric_value: float
    step_number: int
    cost_from_previous: float = 0.0
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    additional_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize waypoint for JSON storage"""
        return {
            'coordinates': self.coordinates.tolist(),
            'metric_value': float(self.metric_value),
            'step_number': int(self.step_number),
            'cost_from_previous': float(self.cost_from_previous),
            'timestamp': float(self.timestamp),
            'additional_metrics': self.additional_metrics
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Waypoint':
        """Deserialize waypoint from dictionary"""
        return cls(
            coordinates=np.array(data['coordinates']),
            metric_value=data['metric_value'],
            step_number=data['step_number'],
            cost_from_previous=data.get('cost_from_previous', 0.0),
            timestamp=data.get('timestamp', datetime.now().timestamp()),
            additional_metrics=data.get('additional_metrics', {})
        )


@dataclass
class Trajectory:
    """
    Represents a complete agent exploration trajectory.
    
    Attributes:
        trajectory_id: Unique identifier for this trajectory
        agent_id: Identifier of the agent that created this trajectory
        waypoints: List of Waypoint objects in sequence
        start_point: Initial point in the trajectory
        parameters: Configuration parameters used during exploration
        status: Current status of the trajectory (active, completed, etc.)
        acquisition_score: Α(τ) score for trajectory-level BO
        saw_compatible: Whether trajectory satisfies SAW constraints
        metadata: Additional metadata about the trajectory
    """
    trajectory_id: str
    agent_id: str
    waypoints: List[Waypoint]
    start_point: np.ndarray
    parameters: Dict[str, Any]
    status: TrajectoryStatus = TrajectoryStatus.COMPLETED
    acquisition_score: float = 0.0
    saw_compatible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize trajectory for storage"""
        return {
            'trajectory_id': self.trajectory_id,
            'agent_id': self.agent_id,
            'waypoints': [wp.to_dict() for wp in self.waypoints],
            'start_point': self.start_point.tolist(),
            'parameters': self.parameters,
            'status': self.status.value,
            'acquisition_score': float(self.acquisition_score),
            'saw_compatible': self.saw_compatible,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trajectory':
        """Deserialize trajectory from dictionary"""
        status_str = data.get('status', 'completed')
        status = TrajectoryStatus(status_str)
        
        return cls(
            trajectory_id=data['trajectory_id'],
            agent_id=data['agent_id'],
            waypoints=[Waypoint.from_dict(wp) for wp in data.get('waypoints', [])],
            start_point=np.array(data['start_point']),
            parameters=data.get('parameters', {}),
            status=status,
            acquisition_score=data.get('acquisition_score', 0.0),
            saw_compatible=data.get('saw_compatible', True),
            metadata=data.get('metadata', {})
        )
    
    def best_metric(self) -> float:
        """Returns the best (minimum) metric value on this trajectory"""
        if not self.waypoints:
            return float('inf')
        return min(wp.metric_value for wp in self.waypoints)
    
    def best_waypoint(self) -> Optional[Waypoint]:
        """Returns the waypoint with best metric value"""
        if not self.waypoints:
            return None
        return min(self.waypoints, key=lambda wp: wp.metric_value)
    
    def get_path_vectors(self) -> np.ndarray:
        """Returns array of waypoint coordinates (n_waypoints, n_dimensions)"""
        if not self.waypoints:
            return np.array([])
        return np.array([wp.coordinates for wp in self.waypoints])
    
    def get_path_length(self) -> float:
        """Returns total distance traveled along trajectory"""
        if len(self.waypoints) < 2:
            return 0.0
        return sum(wp.cost_from_previous for wp in self.waypoints[1:])


class SAWConstraint:
    """
    Manages self-avoiding walk constraints for trajectory exploration.
    
    Prevents agents from revisiting regions already explored by previous agents
    by maintaining exclusion zones around waypoints.
    """
    
    def __init__(self, exclusion_radius: float, dimensionality: int):
        """
        Initialize SAW constraint manager.
        
        Args:
            exclusion_radius: Radius of exclusion zones around explored points
            dimensionality: Number of dimensions in search space
        """
        self.exclusion_radius = exclusion_radius
        self.dimensionality = dimensionality
        self.explored_points = []
        self.kdtree = None
        self._build_kdtree()
    
    def _build_kdtree(self):
        """Build KD-tree for efficient nearest neighbor queries"""
        if not self.explored_points:
            self.kdtree = None
            return
        
        try:
            from scipy.spatial import cKDTree
            self.kdtree = cKDTree(np.array(self.explored_points))
        except ImportError:
            logger.warning("scipy not available; KD-tree acceleration disabled")
            self.kdtree = None
    
    def add_explored_region(self, point: np.ndarray):
        """Mark region around point as explored"""
        self.explored_points.append(np.array(point))
        self._build_kdtree()
    
    def add_trajectory(self, trajectory: Trajectory):
        """Add all waypoints from trajectory to explored regions"""
        for waypoint in trajectory.waypoints:
            self.add_explored_region(waypoint.coordinates)
    
    def is_valid(self, point: np.ndarray) -> bool:
        """Check if point violates SAW constraint (not in exclusion zone)"""
        if not self.explored_points:
            return True
        
        point = np.array(point)
        
        if self.kdtree is not None:
            distance, _ = self.kdtree.query(point, k=1)
            return distance > self.exclusion_radius
        else:
            # Fallback: linear search if KD-tree unavailable
            min_distance = min(np.linalg.norm(point - p) for p in self.explored_points)
            return min_distance > self.exclusion_radius
    
    def compute_penalty(self, point: np.ndarray) -> float:
        """
        Compute SAW penalty for a point.
        
        Returns value in [0, 1]:
        - 1.0: No penalty (outside exclusion zones)
        - 0.0-1.0: Exponential decay penalty (inside exclusion zones)
        - 0.0: Forbidden (at explored point)
        """
        if not self.explored_points:
            return 1.0
        
        point = np.array(point)
        
        if self.kdtree is not None:
            distance, _ = self.kdtree.query(point, k=1)
        else:
            distance = min(np.linalg.norm(point - p) for p in self.explored_points)
        
        if distance > self.exclusion_radius:
            return 1.0  # No penalty
        
        # Exponential decay penalty for points within exclusion radius
        # penalty = exp(-5 * (radius - distance) / radius)
        penalty = np.exp(-5.0 * (self.exclusion_radius - distance) / self.exclusion_radius)
        return float(penalty)
    
    def merge_trajectories(
        self, 
        trajectories: List[Trajectory],
        merge_strategy: str = 'best_per_region'
    ) -> Trajectory:
        """
        Merge multiple trajectories while respecting SAW constraints.
        
        Args:
            trajectories: List of trajectories to merge
            merge_strategy: Strategy for selecting waypoints ('best_per_region', 'all')
        
        Returns:
            Merged trajectory with SAW property satisfied
        """
        merged_waypoints = []
        local_saw = SAWConstraint(self.exclusion_radius, self.dimensionality)
        
        # Sort trajectories by best metric (exploitation priority)
        sorted_trajs = sorted(
            trajectories,
            key=lambda t: t.best_metric()
        )
        
        for trajectory in sorted_trajs:
            for waypoint in trajectory.waypoints:
                # Only add waypoint if it doesn't violate SAW
                if local_saw.is_valid(waypoint.coordinates):
                    merged_waypoints.append(waypoint)
                    local_saw.add_explored_region(waypoint.coordinates)
        
        # Create merged trajectory
        merged = Trajectory(
            trajectory_id=f"merged_{len(trajectories)}_{datetime.now().timestamp()}",
            agent_id="system",
            waypoints=merged_waypoints,
            start_point=sorted_trajs[0].start_point if sorted_trajs else np.array([]),
            parameters={
                'merge_strategy': merge_strategy,
                'source_trajectories': len(trajectories)
            },
            status=TrajectoryStatus.MERGED,
            saw_compatible=True
        )
        
        logger.info(f"Merged {len(trajectories)} trajectories into {len(merged_waypoints)} waypoints")
        
        return merged


class TrajectoryAcquisitionFunction:
    """
    Multi-objective acquisition function for trajectory-level Bayesian optimization.
    
    Evaluates complete trajectories using:
        Α(τ) = w1·Exploit(τ) + w2·Explore(τ) + w3·Coherence(τ)
    """
    
    def __init__(
        self,
        w_exploit: float = 0.5,
        w_explore: float = 0.3,
        w_coherence: float = 0.2
    ):
        """
        Initialize acquisition function.
        
        Args:
            w_exploit: Weight for exploitation term [0, 1]
            w_explore: Weight for exploration term [0, 1]
            w_coherence: Weight for coherence term [0, 1]
        """
        # Normalize weights
        total = w_exploit + w_explore + w_coherence
        self.w_exploit = w_exploit / total
        self.w_explore = w_explore / total
        self.w_coherence = w_coherence / total
        
        logger.info(f"Initialized TrajectoryAF: exploit={self.w_exploit:.3f}, "
                   f"explore={self.w_explore:.3f}, coherence={self.w_coherence:.3f}")
    
    def exploit_term(self, trajectory: Trajectory) -> float:
        """
        Exploitation term: best metric on trajectory.
        Normalized to [0, 1] range (lower is better).
        """
        best = trajectory.best_metric()
        # Assume reasonable bound is 1.0 (adjust based on problem)
        return np.clip(best / 1.0, 0.0, 1.0)
    
    def explore_term(self, trajectory: Trajectory) -> float:
        """
        Exploration term: entropy of waypoint distribution.
        Favors trajectories covering diverse regions.
        """
        if len(trajectory.waypoints) < 2:
            return 0.0
        
        coordinates = trajectory.get_path_vectors()
        n_bins = max(5, int(np.log2(len(trajectory.waypoints))))  # Adaptive binning
        
        try:
            # Discretize coordinates into bins
            bins_occupied = set()
            for coord in coordinates:
                bin_indices = tuple((coord * n_bins).astype(int))
                bins_occupied.add(bin_indices)
            
            # Entropy: normalized to [0, 1]
            total_possible_bins = n_bins ** coordinates.shape[1]
            coverage_ratio = len(bins_occupied) / total_possible_bins
            entropy = -coverage_ratio * np.log(coverage_ratio + 1e-10)
            return entropy / np.log(n_bins)
        except Exception as e:
            logger.warning(f"Error computing explore term: {e}")
            return 0.5
    
    def coherence_term(self, trajectory: Trajectory) -> float:
        """
        Coherence term: inverse of path variance.
        Favors smooth, reproducible trajectories.
        """
        if len(trajectory.waypoints) < 2:
            return 1.0
        
        try:
            coordinates = trajectory.get_path_vectors()
            step_sizes = np.linalg.norm(np.diff(coordinates, axis=0), axis=1)
            
            if len(step_sizes) > 1:
                step_std = np.std(step_sizes)
            else:
                step_std = 0.0
            
            # Coherence = 1 / (1 + std(steps))
            coherence = 1.0 / (1.0 + step_std)
            return np.clip(coherence, 0.0, 1.0)
        except Exception as e:
            logger.warning(f"Error computing coherence term: {e}")
            return 0.5
    
    def evaluate(self, trajectory: Trajectory) -> float:
        """
        Compute acquisition function score Α(τ) for trajectory.
        
        Returns:
            Score in [0, 1] range
        """
        exploit = self.exploit_term(trajectory)
        explore = self.explore_term(trajectory)
        coherence = self.coherence_term(trajectory)
        
        acquisition = (
            self.w_exploit * exploit +
            self.w_explore * explore +
            self.w_coherence * coherence
        )
        
        return np.clip(acquisition, 0.0, 1.0)


class TrajectoryBayesianOptimizer:
    """
    Bayesian optimization at the trajectory level.
    
    Selects optimal trajectories from candidates based on acquisition function.
    """
    
    def __init__(
        self,
        acq_fn: TrajectoryAcquisitionFunction,
        surrogate_model: Optional[Any] = None
    ):
        """
        Initialize optimizer.
        
        Args:
            acq_fn: TrajectoryAcquisitionFunction instance
            surrogate_model: Optional surrogate model (e.g., GaussianProcess)
        """
        self.acq_fn = acq_fn
        self.surrogate_model = surrogate_model
        self.training_data = []
    
    def train_surrogate(self, trajectories: List[Trajectory]):
        """
        Train surrogate model on waypoints from trajectories.
        
        Args:
            trajectories: List of trajectories to train on
        """
        if not self.surrogate_model:
            logger.warning("No surrogate model configured; skipping training")
            return
        
        X_train = []
        y_train = []
        
        for traj in trajectories:
            for waypoint in traj.waypoints:
                X_train.append(waypoint.coordinates)
                y_train.append(waypoint.metric_value)
        
        if not X_train:
            logger.warning("No training data available")
            return
        
        try:
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            self.surrogate_model.fit(X_train, y_train)
            self.training_data.append((X_train, y_train))
            logger.info(f"Trained surrogate on {len(X_train)} waypoints")
        except Exception as e:
            logger.error(f"Error training surrogate: {e}")
    
    def select_optimal_trajectories(
        self,
        candidates: List[Trajectory],
        threshold_quantile: float = 0.2
    ) -> List[Trajectory]:
        """
        Select trajectories achieving global minimum acquisition.
        
        Args:
            candidates: List of candidate trajectories
            threshold_quantile: Quantile threshold (keep top threshold_quantile%)
        
        Returns:
            List of selected trajectories
        """
        if not candidates:
            return []
        
        # Evaluate acquisition function for all candidates
        scores = [self.acq_fn.evaluate(traj) for traj in candidates]
        scores = np.array(scores)
        
        # Find threshold (top quantile)
        threshold = np.quantile(scores, 1.0 - threshold_quantile)
        
        # Select trajectories above threshold
        selected = [
            traj for traj, score in zip(candidates, scores)
            if score >= threshold
        ]
        
        logger.info(f"Selected {len(selected)} of {len(candidates)} trajectories "
                   f"(threshold: {threshold:.3f}, top {threshold_quantile*100:.0f}%)")
        
        # Store scores in trajectory metadata
        for traj, score in zip(candidates, scores):
            traj.acquisition_score = float(score)
        
        return selected


# Utility functions

def create_trajectory_from_points(
    trajectory_id: str,
    agent_id: str,
    points: List[np.ndarray],
    metrics: List[float],
    **kwargs
) -> Trajectory:
    """
    Convenience function to create trajectory from point and metric lists.
    
    Args:
        trajectory_id: Unique trajectory identifier
        agent_id: Agent that created this trajectory
        points: List of n-dimensional points
        metrics: List of metric values at each point
        **kwargs: Additional parameters
    
    Returns:
        Trajectory object
    """
    waypoints = []
    prev_cost = 0.0
    
    for step, (point, metric) in enumerate(zip(points, metrics)):
        if step > 0:
            prev_cost = float(np.linalg.norm(np.array(point) - np.array(points[step-1])))
        
        waypoint = Waypoint(
            coordinates=np.array(point),
            metric_value=float(metric),
            step_number=step,
            cost_from_previous=prev_cost
        )
        waypoints.append(waypoint)
    
    trajectory = Trajectory(
        trajectory_id=trajectory_id,
        agent_id=agent_id,
        waypoints=waypoints,
        start_point=np.array(points[0]) if points else np.array([]),
        parameters=kwargs
    )
    
    return trajectory


def save_trajectory(trajectory: Trajectory, filepath: Path):
    """Save trajectory to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(trajectory.to_dict(), f, indent=2)
    logger.info(f"Saved trajectory to {filepath}")


def load_trajectory(filepath: Path) -> Trajectory:
    """Load trajectory from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    trajectory = Trajectory.from_dict(data)
    logger.info(f"Loaded trajectory from {filepath}")
    return trajectory



# ============================================================================
# AUDITING MODULE (NEW)
# ============================================================================

class AuditAction(Enum):
    """Types of actions recorded in audit log"""
    TRAJECTORY_CAPTURED = "trajectory_captured"
    TRAJECTORY_MERGED = "trajectory_merged"
    TRAJECTORY_PRUNED = "trajectory_pruned"
    TRAJECTORY_INHERITED = "trajectory_inherited"
    ANOMALY_DETECTED = "anomaly_detected"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"


@dataclass
class AuditEvent:
    """Represents a single audit log entry"""
    action: AuditAction
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    trajectory_id: Optional[str] = None
    agent_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)
    severity: str = "INFO"  # INFO, WARNING, ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize audit event"""
        return {
            'action': self.action.value,
            'timestamp': self.timestamp,
            'trajectory_id': self.trajectory_id,
            'agent_id': self.agent_id,
            'details': self.details,
            'environment': self.environment,
            'severity': self.severity
        }
    
    def __str__(self) -> str:
        """Human-readable audit event"""
        return (f"[{self.severity}] {self.action.value} - "
                f"traj:{self.trajectory_id or 'N/A'} "
                f"agent:{self.agent_id or 'N/A'}")


class TrajectoryAuditLog:
    """
    Maintains append-only audit log for trajectory operations.
    
    Features:
    - Immutable event log (append-only)
    - Timestamp ordering
    - Efficient querying by agent/trajectory/time
    - Anomaly detection and flagging
    """
    
    def __init__(self, max_events: int = 10000):
        """
        Initialize audit log.
        
        Args:
            max_events: Maximum events to keep (FIFO on overflow)
        """
        self.events: List[AuditEvent] = []
        self.max_events = max_events
        self.event_index = {}  # Quick lookup by trajectory_id
    
    def log_event(self, event: AuditEvent):
        """Record an audit event (append-only)"""
        self.events.append(event)
        
        # Update index
        if event.trajectory_id:
            if event.trajectory_id not in self.event_index:
                self.event_index[event.trajectory_id] = []
            self.event_index[event.trajectory_id].append(len(self.events) - 1)
        
        # Trim if over max
        if len(self.events) > self.max_events:
            removed = self.events.pop(0)
            logger.warning(f"Audit log overflow: removed oldest event {removed.action}")
    
    def log_capture(self, trajectory: Trajectory):
        """Log trajectory capture event"""
        event = AuditEvent(
            action=AuditAction.TRAJECTORY_CAPTURED,
            trajectory_id=trajectory.trajectory_id,
            agent_id=trajectory.agent_id,
            details={
                'waypoint_count': len(trajectory.waypoints),
                'best_metric': trajectory.best_metric(),
                'acquisition_score': trajectory.acquisition_score,
                'path_length': trajectory.get_path_length()
            },
            environment=self._capture_environment()
        )
        self.log_event(event)
        logger.info(f"Audit: Captured {event}")
    
    def log_merge(self, source_ids: List[str], merged_id: str, 
                  input_count: int, output_count: int):
        """Log trajectory merge event"""
        event = AuditEvent(
            action=AuditAction.TRAJECTORY_MERGED,
            trajectory_id=merged_id,
            agent_id="system",
            details={
                'source_trajectories': source_ids,
                'input_waypoints': input_count,
                'output_waypoints': output_count,
                'waypoints_removed': input_count - output_count,
                'saw_preserved': True
            }
        )
        self.log_event(event)
        logger.info(f"Audit: Merged {len(source_ids)} trajectories → {output_count} waypoints")
    
    def log_prune(self, candidates: List[str], selected: List[str], 
                  scores: Dict[str, float]):
        """Log trajectory pruning event"""
        event = AuditEvent(
            action=AuditAction.TRAJECTORY_PRUNED,
            agent_id="system",
            details={
                'candidate_count': len(candidates),
                'selected_count': len(selected),
                'selected_trajectories': selected,
                'scores': scores,
                'selection_rate': len(selected) / len(candidates) if candidates else 0
            }
        )
        self.log_event(event)
        logger.info(f"Audit: Pruned {len(candidates)} → {len(selected)} trajectories")
    
    def log_inheritance(self, source_agent: str, target_agent: str,
                       inherited_ids: List[str]):
        """Log trajectory inheritance event"""
        event = AuditEvent(
            action=AuditAction.TRAJECTORY_INHERITED,
            agent_id=target_agent,
            details={
                'source_agent': source_agent,
                'inherited_trajectory_ids': inherited_ids,
                'inheritance_count': len(inherited_ids)
            }
        )
        self.log_event(event)
        logger.info(f"Audit: Agent {target_agent} inherited {len(inherited_ids)} trajectories from {source_agent}")
    
    def log_anomaly(self, trajectory_id: str, anomaly_type: str, 
                   severity: str, details: Dict[str, Any]):
        """Log detected anomaly"""
        event = AuditEvent(
            action=AuditAction.ANOMALY_DETECTED,
            trajectory_id=trajectory_id,
            severity=severity,
            details={
                'anomaly_type': anomaly_type,
                **details
            }
        )
        self.log_event(event)
        logger.warning(f"Audit: {severity} - {anomaly_type} in {trajectory_id}")
    
    def query_by_trajectory(self, trajectory_id: str) -> List[AuditEvent]:
        """Get all events related to a trajectory"""
        if trajectory_id not in self.event_index:
            return []
        return [self.events[i] for i in self.event_index[trajectory_id]]
    
    def query_by_agent(self, agent_id: str) -> List[AuditEvent]:
        """Get all events by an agent"""
        return [e for e in self.events if e.agent_id == agent_id]
    
    def query_by_time_range(self, start_time: float, end_time: float) -> List[AuditEvent]:
        """Get all events within time range"""
        return [e for e in self.events 
                if start_time <= e.timestamp <= end_time]
    
    def query_by_action(self, action: AuditAction) -> List[AuditEvent]:
        """Get all events of a specific action type"""
        return [e for e in self.events if e.action == action]
    
    def detect_anomalies(self, trajectories: List[Trajectory]) -> List[Dict[str, Any]]:
        """
        Detect anomalies in trajectories.
        
        Returns:
            List of anomalies found
        """
        anomalies = []
        
        for traj in trajectories:
            # Check 1: Low coherence
            acq_fn = TrajectoryAcquisitionFunction()
            coherence = acq_fn.coherence_term(traj)
            if coherence < 0.3:
                anomalies.append({
                    'trajectory_id': traj.trajectory_id,
                    'type': 'low_coherence',
                    'severity': 'WARNING',
                    'value': coherence,
                    'threshold': 0.3
                })
                self.log_anomaly(traj.trajectory_id, 'low_coherence', 
                               'WARNING', {'coherence_score': coherence})
            
            # Check 2: Metric divergence
            if len(traj.waypoints) > 1:
                metrics = [wp.metric_value for wp in traj.waypoints]
                increases = sum(1 for i in range(1, len(metrics)) 
                              if metrics[i] > metrics[i-1] * 1.5)
                if increases > len(metrics) * 0.1:  # >10% increases
                    anomalies.append({
                        'trajectory_id': traj.trajectory_id,
                        'type': 'metric_divergence',
                        'severity': 'ERROR',
                        'increase_ratio': increases / len(metrics)
                    })
                    self.log_anomaly(traj.trajectory_id, 'metric_divergence',
                                   'ERROR', {'increase_ratio': increases / len(metrics)})
            
            # Check 3: SAW violations
            if not traj.saw_compatible:
                anomalies.append({
                    'trajectory_id': traj.trajectory_id,
                    'type': 'saw_violation',
                    'severity': 'ERROR',
                    'message': 'Trajectory does not satisfy SAW constraints'
                })
                self.log_anomaly(traj.trajectory_id, 'saw_violation',
                               'ERROR', {'saw_compatible': False})
        
        return anomalies
    
    def verify_reproducibility(self, trajectory: Trajectory) -> bool:
        """
        Verify trajectory reproducibility.
        
        Returns:
            True if trajectory can be reproduced
        """
        try:
            # Compute hash of trajectory data
            checksum = self._compute_trajectory_hash(trajectory)
            
            if trajectory.metadata.get('reproducibility_checksum') == checksum:
                event = AuditEvent(
                    action=AuditAction.VERIFICATION_PASSED,
                    trajectory_id=trajectory.trajectory_id,
                    details={'verification_type': 'reproducibility'}
                )
                self.log_event(event)
                return True
            else:
                event = AuditEvent(
                    action=AuditAction.VERIFICATION_FAILED,
                    trajectory_id=trajectory.trajectory_id,
                    severity='WARNING',
                    details={
                        'verification_type': 'reproducibility',
                        'expected_hash': trajectory.metadata.get('reproducibility_checksum'),
                        'computed_hash': checksum
                    }
                )
                self.log_event(event)
                return False
        except Exception as e:
            logger.error(f"Error verifying reproducibility: {e}")
            return False
    
    def _capture_environment(self) -> Dict[str, Any]:
        """Capture runtime environment information"""
        return {
            'timestamp': datetime.now().isoformat(),
            'platform': __import__('platform').platform(),
            'python_version': __import__('sys').version,
            'pid': __import__('os').getpid()
        }
    
    def _compute_trajectory_hash(self, trajectory: Trajectory) -> str:
        """Compute reproducibility hash for trajectory"""
        import hashlib
        
        data = f"{trajectory.trajectory_id}_{trajectory.agent_id}_"
        for wp in trajectory.waypoints:
            data += f"{wp.coordinates.tobytes().hex()}_{wp.metric_value}_"
        
        return hashlib.md5(data.encode()).hexdigest()
    
    def export_audit_report(self, filepath: Path):
        """Export audit log to file"""
        report = {
            'export_timestamp': datetime.now().isoformat(),
            'total_events': len(self.events),
            'events': [e.to_dict() for e in self.events]
        }
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Exported audit log to {filepath}")


# Global audit log instance
_audit_log = TrajectoryAuditLog()


def get_audit_log() -> TrajectoryAuditLog:
    """Access global audit log"""
    return _audit_log

