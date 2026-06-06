"""
Evaluator for heilbronn problem for convex regions for n=13 points with improved timeout handling
"""

import numpy as np
import time
import os
import subprocess
import tempfile
import traceback
import sys
import pickle

TOL = 1e-6
TOL_SQ = TOL * TOL
REGION_AREA = 1.0  # Unit square area

class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    """Handle timeout signal"""
    raise TimeoutError("Function execution timed out")

def points_are_close(p1, p2):
    """Check if two points are closer than a tolerance threshold."""
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return dx * dx + dy * dy < TOL_SQ

def triangle_area(a, b, c):
    """Calculate area of triangle given three vertices using cross product."""
    return 0.5 * abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))


def verify_solution(points, min_area):
    """Validate solution correctness and constraints."""
    n = len(points)

    # Check all points are within [0,1]x[0,1]
    for p in points:
        if not (0 <= p[0] <= 1 and 0 <= p[1] <= 1):
            return False

    # Check minimum point separation
    for i in range(n):
        for j in range(i + 1, n):
            if points_are_close(points[i], points[j]):
                return False

    # Verify actual minimum area matches reported
    min_computed = float('inf')
    for i in range(n):
        for j in range(i + 1, n):
            for k in range(j + 1, n):
                area = triangle_area(points[i], points[j], points[k])
                if area < 1e-10:  # Degenerate triangle check
                    return False
                if area < min_computed:
                    min_computed = area

    return abs(min_computed - min_area) < 1e-5

def run_with_timeout(program_path, timeout_seconds=20):
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        # Write a script that executes the program and saves results
        script = f"""
import sys
import numpy as np
import os
import pickle
import traceback

# Add the directory to sys.path
sys.path.insert(0, os.path.dirname('{program_path}'))

# Debugging info
print(f"Running in subprocess, Python version: {{sys.version}}")
print(f"Program path: {program_path}")

try:
    # Import the program
    spec = __import__('importlib.util').util.spec_from_file_location("program", '{program_path}')
    program = __import__('importlib.util').util.module_from_spec(spec)
    spec.loader.exec_module(program)

    # Run the search point function
    print("Calling simulate_heilbronn()...")
    best_overall_points, best_overall_min_area, best_area_ratio = program.simulate_heilbronn(n=13)
    print(f"simulate_heilbronn() returned successfully: best_area_ratio = {{best_area_ratio}}")

    # Save results to a file
    results = {{
        'best_overall_points': best_overall_points,
        'best_overall_min_area': best_overall_min_area,
        'best_area_ratio': best_area_ratio
    }}

    with open('{temp_file.name}.results', 'wb') as f:
        pickle.dump(results, f)
    print(f"Results saved to {temp_file.name}.results")

except Exception as e:
    # If an error occurs, save the error instead
    print(f"Error in subprocess: {{str(e)}}")
    traceback.print_exc()
    with open('{temp_file.name}.results', 'wb') as f:
        pickle.dump({{'error': str(e)}}, f)
    print(f"Error saved to {temp_file.name}.results")
"""
        temp_file.write(script.encode())
        temp_file_path = temp_file.name

    results_path = f"{temp_file_path}.results"

    try:
        # Run the script with timeout
        process = subprocess.Popen(
            [sys.executable, temp_file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            exit_code = process.returncode

            # Always print output for debugging purposes
            print(f"Subprocess stdout: {stdout.decode()}")
            if stderr:
                print(f"Subprocess stderr: {stderr.decode()}")

            # Still raise an error for non-zero exit codes, but only after printing the output
            if exit_code != 0:
                raise RuntimeError(f"Process exited with code {exit_code}")

            # Load the results
            if os.path.exists(results_path):
                with open(results_path, "rb") as f:
                    results = pickle.load(f)

                # Check if an error was returned
                if "error" in results:
                    raise RuntimeError(f"Program execution failed: {results['error']}")

                return results["best_overall_points"], results["best_overall_min_area"], results["best_area_ratio"]
            else:
                raise RuntimeError("Results file not found")

        except subprocess.TimeoutExpired:
            # Kill the process if it times out
            process.kill()
            process.wait()
            raise TimeoutError(f"Process timed out after {timeout_seconds} seconds")

    finally:
        # Clean up temporary files
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if os.path.exists(results_path):
            os.unlink(results_path)


def evaluate(program_path):
    """
    Evaluate the program by running it once and checking area

    Args:
        program_path: Path to the program file

    Returns:
        Dictionary of metrics
    """
    # Target value from the paper
    TARGET_VALUE = 0.0309  # AlphaEvolve result for n=13

    try:
        # For constructor-based approaches, a single evaluation is sufficient
        # since the result is deterministic
        start_time = time.time()

        # Use subprocess to run with timeout
        best_overall_points, best_overall_min_area, best_area_ratio = run_with_timeout(
            program_path, timeout_seconds=600  # Single timeout
        )

        end_time = time.time()
        eval_time = end_time - start_time

        if not isinstance(best_overall_points, np.ndarray):
            best_overall_points = np.array(best_overall_points)

        valid = verify_solution(best_overall_points, best_overall_min_area)

        # Target ratio (how close we are to the target)
        target_ratio = best_area_ratio / TARGET_VALUE if valid else 0.0

        validity = 1.0 if valid else 0.0

        # Combined score - higher is better
        combined_score = target_ratio * validity

        print(
            f"Evaluation: valid={valid}, best_area_ratio={best_area_ratio:.6f}, target={TARGET_VALUE}, ratio={target_ratio:.6f}, time={eval_time:.2f}s"
        )

        return {
            "best_area_ratio": float(best_area_ratio),
            "target_ratio": float(target_ratio),
            "validity": float(validity),
            "combined_score": float(combined_score),
        }

    except Exception as e:
        print(f"Evaluation failed completely: {str(e)}")
        traceback.print_exc()
        return {
            "best_area_ratio": 0.0,
            "target_ratio": 0.0,
            "validity": 0.0,
            "combined_score": 0.0,
        }

if __name__ == "__main__":
    result = evaluate("./best_solution.py")
    print(f"Best_area_ratio: {result['best_area_ratio']:.6f}")
    print(f"Target_ratio: {result['target_ratio']:.6f}")
    print(f"Validity: {result['validity']}")
    print(f"Combined_score: {result['combined_score']:.6f}")