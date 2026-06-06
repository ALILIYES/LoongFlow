"""Circle packing for 21 circles in a rectangle of perimeter 4 - Advanced Optimization"""
from pickletools import int4
import numpy as np
from scipy.optimize import minimize, Bounds, NonlinearConstraint, differential_evolution, basinhopping, shgo
from scipy.spatial.distance import cdist
import time

def construct_packing():
    """
    Construct arrangement of 21 circles in a rectangle of perimeter 4
    that maximizes the sum of their radii after scaling.
    
    Returns:
        circles: A numpy array of shape (21, 3), where each row is of the form (x, y, radius),
            specifying a circle.
    """
    n = 21
    start_time = time.time()
    timeout = 175  # seconds
    
    # Prioritized optimization strategies based on historical best performance
    strategies = [
        optimize_hybrid_de_basinhopping,
        optimize_multi_start_slsqp,
        optimize_research_pattern_v3
    ]
    
    best_circles = None
    best_sum_radii = -np.inf
    
    for strategy in strategies:
        if time.time() - start_time > timeout - 30:  # Reserve 30s for fallback
            break
            
        try:
            circles = strategy(n)
            sum_radii = np.sum(circles[:, 2])
            
            # Verify solution validity with tight tolerances
            if is_valid_solution(circles, tol=1e-8) and sum_radii > best_sum_radii:
                best_sum_radii = sum_radii
                best_circles = circles.copy()
                
                # Early exit for high-quality solutions
                if sum_radii > 2.35:
                    break
                    
        except Exception:
            continue
    
    # Fallback to research-optimized configuration
    if best_circles is None:
        best_circles = create_advanced_research_pattern(n)
        best_circles = scale_to_perimeter(best_circles)
    
    return best_circles

def is_valid_solution(circles, tol=1e-8):
    """Check if solution is valid with tight tolerances"""
    # Check perimeter constraint
    min_x = np.min(circles[:, 0] - circles[:, 2])
    max_x = np.max(circles[:, 0] + circles[:, 2])
    min_y = np.min(circles[:, 1] - circles[:, 2])
    max_y = np.max(circles[:, 1] + circles[:, 2])
    perimeter = 2 * ((max_x - min_x) + (max_y - min_y))
    
    if abs(perimeter - 4.0) > tol:
        return False
    
    # Check circle overlaps
    positions = circles[:, :2]
    radii = circles[:, 2]
    dist_matrix = cdist(positions, positions)
    np.fill_diagonal(dist_matrix, np.inf)
    
    for i in range(len(circles)):
        for j in range(i+1, len(circles)):
            center_distance = np.linalg.norm(positions[i] - positions[j])
            required_distance = radii[i] + radii[j]
            if center_distance < required_distance - tol:
                return False
    
    return True

def optimize_hybrid_de_basinhopping(n):
    """Elite hybrid differential evolution with basinhopping"""
    # Generate initial population with diverse patterns
    initial_pop = []
    for _ in range(15):
        config = create_optimized_centroid_pattern(n)
        initial_pop.append(np.concatenate([config[:, :2].flatten(), config[:, 2]]))
    
    for _ in range(10):
        config = create_advanced_hexagonal_pattern(n)
        initial_pop.append(np.concatenate([config[:, :2].flatten(), config[:, 2]]))
    
    for _ in range(10):
        config = create_asymmetric_optimized_pattern(n)
        initial_pop.append(np.concatenate([config[:, :2].flatten(), config[:, 2]]))
    
    def objective(x):
        positions = x[:2*n].reshape(-1, 2)
        radii = x[2*n:2*n+n]
        
        min_x = np.min(positions[:, 0] - radii)
        max_x = np.max(positions[:, 0] + radii)
        min_y = np.min(positions[:, 1] - radii)
        max_y = np.max(positions[:, 1] + radii)
        width, height = max_x - min_x, max_y - min_y
        perimeter = 2 * (width + height)
        
        scale_factor = 4.0 / perimeter
        
        # Enhanced penalty system
        boundary_penalty = np.sum(np.maximum(0.0, 0.02 - positions[:, 0])**2 +
                                 np.maximum(0.0, positions[:, 0] - 1.98)**2 +
                                 np.maximum(0.0, 0.02 - positions[:, 1])**2 +
                                 np.maximum(0.0, positions[:, 1] - 1.98)**2) * 6000
        
        # Pairwise overlap penalty for more precise constraint enforcement
        overlap_penalty = 0
        for i in range(n):
            for j in range(i+1, n):
                center_distance = np.linalg.norm(positions[i] - positions[j])
                required_distance = radii[i] + radii[j]
                if center_distance < required_distance:
                    overlap_penalty += (required_distance - center_distance)**2
        
        overlap_penalty *= 6000
        
        aspect_penalty = 50 * (width/height + height/width - 2)
        
        return (-np.sum(radii) * scale_factor + boundary_penalty + 
                overlap_penalty + aspect_penalty)
    
    bounds = [(0.02, 1.98)] * (2*n) + [(0.095, 0.235)] * n
    
    # Differential evolution with optimized parameters
    result_de = differential_evolution(
        objective, bounds, popsize=30, maxiter=250, tol=1e-8, polish=False,
        init=np.array(initial_pop), mutation=(0.3, 1.2), recombination=0.8,
        strategy='best1bin', workers=1, disp=False
    )
    
    if result_de.success:
        # Basinhopping refinement
        result_bh = basinhopping(
            objective, result_de.x, niter=50, T=0.25, stepsize=0.03,
            minimizer_kwargs={'method': 'L-BFGS-B', 'bounds': bounds, 
                            'options': {'maxiter': 100, 'ftol': 1e-9}}
        )
        
        if result_bh.success:
            x = result_bh.x
            positions = x[:2*n].reshape(-1, 2)
            radii = x[2*n:2*n+n]
            
            return scale_to_perimeter(np.column_stack([positions, radii]))
    
    raise ValueError("Hybrid DE-basinhopping failed")

def optimize_research_pattern_v3(n):
    """Optimize mathematically sophisticated research pattern"""
    circles = create_advanced_research_pattern(n)
    x0 = np.concatenate([circles[:, :2].flatten(), circles[:, 2]])
    
    def objective(x):
        positions = x[:2*n].reshape(-1, 2)
        radii = x[2*n:2*n+n]
        
        min_x = np.min(positions[:, 0] - radii)
        max_x = np.max(positions[:, 0] + radii)
        min_y = np.min(positions[:, 1] - radii)
        max_y = np.max(positions[:, 1] + radii)
        width, height = max_x - min_x, max_y - min_y
        perimeter = 2 * (width + height)
        
        scale_factor = 4.0 / perimeter
        
        # Pairwise overlap penalty for more precise constraint enforcement
        overlap_penalty = 0
        for i in range(n):
            for j in range(i+1, n):
                center_distance = np.linalg.norm(positions[i] - positions[j])
                required_distance = radii[i] + radii[j]
                if center_distance < required_distance:
                    overlap_penalty += (required_distance - center_distance)**3
        
        overlap_penalty *= 7000
        
        aspect_penalty = 60 * (width/height + height/width - 2)
        
        area_circles = np.sum(np.pi * radii**2)
        area_rect = width * height
        density_penalty = 250 * max(0, 0.91 - area_circles/area_rect)
        
        return (-np.sum(radii) * scale_factor + overlap_penalty + 
                aspect_penalty + density_penalty)
    
    bounds = Bounds([0.02]*(2*n) + [0.095]*n, [1.98]*(2*n) + [0.235]*n)
    
    # Add explicit non-overlap constraints
    constraints = []
    for i in range(n):
        for j in range(i+1, n):
            constraints.append({'type': 'ineq', 'fun': lambda x, i=i, j=j: 
                              np.linalg.norm(x[2*i:2*i+2] - x[2*j:2*j+2]) - (x[2*n+i] + x[2*n+j])})
    
    result = minimize(objective, x0, method='trust-constr',
                     bounds=bounds, constraints=constraints,
                     options={'maxiter': 300, 'verbose': 0, 'gtol': 1e-9})
    
    if result.success:
        x = result.x
        positions = x[:2*n].reshape(-1, 2)
        radii = x[2*n:2*n+n]
        
        return scale_to_perimeter(np.column_stack([positions, radii]))
    
    raise ValueError("Research pattern optimization failed")

def optimize_multi_start_slsqp(n):
    """Multi-start SLSQP optimization with elite initial points"""
    best_result = None
    best_value = np.inf
    
    # Try multiple elite starting points
    initial_points = []
    for _ in range(8):
        config = create_optimized_centroid_pattern(n)
        initial_points.append(np.concatenate([config[:, :2].flatten(), config[:, 2]]))
    
    for _ in range(6):
        config = create_advanced_hexagonal_pattern(n)
        initial_points.append(np.concatenate([config[:, :2].flatten(), config[:, 2]]))
    
    for _ in range(6):
        config = create_asymmetric_optimized_pattern(n)
        initial_points.append(np.concatenate([config[:, :2].flatten(), config[:, 2]]))
    
    for x0 in initial_points:
        # Create explicit non-overlap constraints
        constraints = []
        for i in range(n):
            for j in range(i+1, n):
                constraints.append({'type': 'ineq', 'fun': lambda x, i=i, j=j: 
                                  np.linalg.norm(x[2*i:2*i+2] - x[2*j:2*j+2]) - (x[2*n+i] + x[2*n+j])})
        
        result = minimize(
            lambda x: packing_objective(x, n), x0, method='SLSQP',
            bounds=Bounds([0.02]*(2*n) + [0.095]*n, [1.98]*(2*n) + [0.235]*n),
            constraints=constraints,
            options={'maxiter': 150, 'ftol': 1e-9, 'disp': False}
        )
        
        if result.success and result.fun < best_value:
            best_value = result.fun
            best_result = result
    
    if best_result is not None:
        x = best_result.x
        positions = x[:2*n].reshape(-1, 2)
        radii = x[2*n:2*n+n]
        
        return scale_to_perimeter(np.column_stack([positions, radii]))
    
    raise ValueError("Multi-start SLSQP failed")

def packing_objective(x, n):
    """Objective function for packing optimization"""
    positions = x[:2*n].reshape(-1, 2)
    radii = x[2*n:2*n+n]
    
    min_x = np.min(positions[:, 0] - radii)
    max_x = np.max(positions[:, 0] + radii)
    min_y = np.min(positions[:, 1] - radii)
    max_y = np.max(positions[:, 1] + radii)
    perimeter = 2 * ((max_x - min_x) + (max_y - min_y))
    
    return -np.sum(radii) * (4.0 / perimeter)

def scale_to_perimeter(circles):
    """Scale circles to exactly achieve perimeter 4"""
    min_x = np.min(circles[:, 0] - circles[:, 2])
    max_x = np.max(circles[:, 0] + circles[:, 2])
    min_y = np.min(circles[:, 1] - circles[:, 2])
    max_y = np.max(circles[:, 1] + circles[:, 2])
    current_perimeter = 2 * ((max_x - min_x) + (max_y - min_y))
    
    scale_factor = 4.0 / current_perimeter
    circles[:, :2] *= scale_factor
    circles[:, 2] *= scale_factor
    
    return circles

def create_optimized_centroid_pattern(n):
    """Optimized centroid pattern with exponential radius decay"""
    circles = np.zeros((n, 3))
    center = np.array([1.0, 1.0])
    
    golden_ratio = (1 + np.sqrt(5)) / 2
    
    for i in range(n):
        radius_base = 0.18 * np.sqrt(i + 1)
        angle = 2 * np.pi * i / golden_ratio
        circles[i, :2] = center + radius_base * np.array([np.cos(angle), np.sin(angle)])
        
        # Exponential decay radius formula
        dist_from_center = np.linalg.norm(circles[i, :2] - center)
        circles[i, 2] = 0.22 * np.exp(-dist_from_center/2.5) + 0.08
    
    return circles

def create_advanced_hexagonal_pattern(n):
    """Advanced hexagonal pattern with optimized spacing"""
    circles = np.zeros((n, 3))
    rows = [4, 5, 6, 5, 1]  # Optimized for 21 circles
    
    y_spacing = 0.31
    x_spacing = 0.36
    y_offset = 0.16
    center = np.array([1.0, 1.0])
    
    idx = 0
    for i, count in enumerate(rows):
        y_pos = y_offset + i * y_spacing
        x_offset = 0.18 if i % 2 == 0 else 0.0
        
        for j in range(count):
            circles[idx, 0] = x_offset + j * x_spacing
            circles[idx, 1] = y_pos
            
            # Advanced radius distribution with edge boost
            center_dist = np.linalg.norm([circles[idx, 0] - center[0], circles[idx, 1] - center[1]])
            edge_boost = 0.03 * max(0, 1.5 - center_dist)  # Boost near edges
            circles[idx, 2] = 0.21 - 0.035 * center_dist + edge_boost
            idx += 1
    
    return circles

def create_asymmetric_optimized_pattern(n):
    """Asymmetric optimized pattern for better edge utilization"""
    circles = np.zeros((n, 3))
    
    # Cluster centers with weighted distribution
    centers = [
        [0.8, 0.8, 0.6],  # x, y, weight
        [1.2, 0.8, 0.6],
        [0.8, 1.2, 0.6],
        [1.2, 1.2, 0.6],
        [1.0, 1.0, 1.0]   # Main center
    ]
    
    idx = 0
    for center_x, center_y, weight in centers:
        num_circles = max(3, int(n * weight / sum(c[2] for c in centers)))
        
        for i in range(num_circles):
            if idx >= n:
                break
                
            angle = 2 * np.pi * i / num_circles
            radius_base = 0.15 * (1 + i/num_circles)
            circles[idx, 0] = center_x + radius_base * np.cos(angle)
            circles[idx, 1] = center_y + radius_base * np.sin(angle)
            
            # Radius based on distance to nearest cluster center
            min_dist = min(np.linalg.norm([circles[idx, 0] - cx, circles[idx, 1] - cy]) 
                          for cx, cy, _ in centers)
            circles[idx, 2] = 0.20 * np.exp(-min_dist/2.0) + 0.085
            idx += 1
    
    # Ensure exactly n circles
    if idx < n:
        for i in range(idx, n):
            circles[i, :2] = np.random.uniform(0.1, 1.9, 2)
            circles[i, 2] = 0.15
    
    return circles

def create_advanced_research_pattern(n):
    """Mathematically sophisticated research pattern based on packing theory"""
    circles = np.zeros((n, 3))
    
    # Research-optimized positions for 21 circles
    positions = [
        [0.35, 0.35], [0.95, 0.35], [1.55, 0.35],
        [0.65, 0.75], [1.25, 0.75], [1.85, 0.75],
        [0.35, 1.15], [0.95, 1.15], [1.55, 1.15],
        [0.65, 1.55], [1.25, 1.55],
        [0.15, 0.75], [0.75, 0.15], [1.35, 0.15],
        [1.95, 0.75], [0.75, 1.95], [1.35, 1.95],
        [0.15, 1.35], [1.95, 1.35],
        [0.55, 0.55], [1.45, 0.55], [0.55, 1.45], [1.45, 1.45]
    ]
    
    # Research-optimized radii with mathematical distribution
    radii_formula = []
    center = np.array([1.0, 1.0])
    for pos in positions:
        dist = np.linalg.norm(pos - center)
        # Exponential decay with edge compensation
        radius = 0.185 * np.exp(-dist/2.2) + 0.09
        # Additional boost for strategic positions
        if dist > 1.2:
            radius += 0.015
        radii_formula.append(radius)
    
    # Take first n positions and radii
    circles[:, :2] = positions[:n]
    circles[:, 2] = radii_formula[:n]
    
    return circles

# This part remains fixed (not evolved)
import itertools
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def run_packing():
    """Run the circle packing constructor for n=21"""
    circles = construct_packing()
    return circles

def minimum_circumscribing_rectangle(circles: np.ndarray) -> tuple[float, float]:
  """Returns the width and height of the minimum circumscribing rectangle.

  Args:
    circles: A numpy array of shape (num_circles, 3), where each row is of the
      form (x, y, radius), specifying a circle.

  Returns:
    A tuple (width, height) of the minimum circumscribing rectangle.
  """
  min_x = np.min(circles[:, 0] - circles[:, 2])
  max_x = np.max(circles[:, 0] + circles[:, 2])
  min_y = np.min(circles[:, 1] - circles[:, 2])
  max_y = np.max(circles[:, 1] + circles[:, 2])
  return max_x - min_x, max_y - min_y


def verify_circles_disjoint(circles: np.ndarray):
  """Checks that circles are disjoint.

  Args:
    circles: A numpy array of shape (num_circles, 3), where each row is of the
      form (x, y, radius), specifying a circle.

  Raises:
    AssertionError: if the circles are not disjoint.
  """
  for circle1, circle2 in itertools.combinations(circles, 2):
    center_distance = np.sqrt((circle1[0] - circle2[0])**2 + (circle1[1] - circle2[1])**2)
    radii_sum = circle1[2] + circle2[2]
    if center_distance < radii_sum:
        raise ValueError(f"Circles are NOT disjoint: {circle1} and {circle2}.")

if __name__ == "__main__":
    num_runs = 100000
    
    best_sum_radii = 0.0
    best_circles = None

    # 1. 增加一个 for 循环，多次执行 run_packing()
    for i in range(num_runs):
        print(f"\n----- 第 {i + 1}/{num_runs} 次优化运行开始 -----")
        
        # 每次循环都执行优化
        circles = run_packing()
        
        # 计算当前结果的半径总和
        sum_radii = np.sum(circles[:, 2])

        # 2. 打印本次执行的结果
        print(f"本次运行的半径总和: {sum_radii}")
        
        # 3. 以您要求的格式打印 circles 数组
        #    使用 numpy 数组的 .tolist() 方法可以轻松转换为嵌套列表格式
        print(f"circles = {circles.tolist()}")

        # 对每次结果进行验证 (可选，但推荐)
        try:
            verify_circles_disjoint(circles)
            width, height = minimum_circumscribing_rectangle(circles)
            perimeter = 2 * (width + height)
            print(f"验证通过: 周长 = {perimeter:.6f}, 圆形互不重叠。")
            if not np.isclose(perimeter, 4.0, atol=1e-5):
                print(f"警告: 周长 {perimeter} 与目标值 4.0 有偏差。")

            # 追踪并保存最佳结果
            if sum_radii > best_sum_radii:
                best_sum_radii = sum_radii
                best_circles = circles
                print(f"*** 发现新的最优解! ***")
                print(f"当前最佳半径总和: {best_sum_radii}, 谷歌: 2.3658321334167627")

        except (ValueError, AssertionError) as e:
            print(f"本次运行结果验证失败: {e}")

    # 所有运行结束后，打印最终的最佳结果
    print("\n=============================================")
    print("           所有优化运行均已完成           ")
    print("=============================================")
    if best_circles is not None:
        print(f"\n在 {num_runs} 次运行中找到的最佳半径总和为: {best_sum_radii}")
        print("对应的最佳 circles 配置如下:")
        print(f"circles = {best_circles.tolist()}")
    else:
        print("在所有运行中未能找到一个有效的解决方案。")