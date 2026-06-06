"""
Evaluator for circle packing example (n=21) with improved timeout handling
Enhanced with artifacts to demonstrate execution feedback
"""

import itertools
import os
import pickle
import subprocess
import sys
import tempfile
import time
import traceback

import numpy as np

num_circles = 21


class TimeoutError(Exception):
    """Custom timeout exception"""

    pass


def timeout_handler(signum, frame):
    """Handle timeout signal"""
    raise TimeoutError("Function execution timed out")


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


def validate_packing(circles: np.ndarray):
    """
    Validate that circles don't overlap and are inside a rectangle of perimeter 4.

    Args:
        circles: A numpy array of shape (num_circles, 3), where each row is of the
         form (x, y, radius), specifying a circle.

    Returns:
        Tuple of (is_valid: bool, validation_details: dict)
    """

    num_circles = len(circles)

    validation_details = {
        "total_circles": num_circles,
        "overlaps_check": [],
        "perimeter_check": [],
        "min_radius": float(np.min(circles[:, 2])),
        "max_radius": float(np.max(circles[:, 2])),
        "avg_radius": float(np.mean(circles[:, 2])),
        "perimeter": 0.0,
        "error_message": "",
    }

    # Checks that circles are disjoint
    for circle1, circle2 in itertools.combinations(circles, 2):
        center_distance = np.sqrt(
            (circle1[0] - circle2[0]) ** 2 + (circle1[1] - circle2[1]) ** 2
        )
        radii_sum = circle1[2] + circle2[2]
        if center_distance < radii_sum:
            violation = f"Circles are NOT disjoint: {circle1} and {circle2}."
            validation_details["overlaps_check"].append(violation)
            validation_details["error_message"] += violation + "\n"
            print(violation)

    # Checks rectangle of perimeter 4
    width, height = minimum_circumscribing_rectangle(circles)
    perimeter = 2 * (width + height)
    validation_details["perimeter"] = perimeter
    if (width + height) > 2:
        violation = f"Perimeter of minimum circumscribing rectangle: {perimeter:.6f}, not equal to 4"
        validation_details["perimeter_check"].append(violation)
        validation_details["error_message"] += violation + "\n"
        print(violation)

    is_valid = (
        len(validation_details["overlaps_check"]) == 0
        and len(validation_details["perimeter_check"]) == 0
    )

    validation_details["is_valid"] = is_valid

    return is_valid, validation_details


def run_with_timeout(program_path, timeout_seconds=20):
    """
    Run the program in a separate process with timeout
    using a simple subprocess approach

    Args:
        program_path: Path to the program file
        timeout_seconds: Maximum execution time in seconds

    Returns:
        circles from the program
    """
    # Create a temporary file to execute
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
    
    # Run the packing function
    print("Calling construct_packing()...")
    circles = program.construct_packing()
    print(f"construct_packing() returned successfully: circles = {{circles}}")

    # Save results to a file
    results = {{
        'circles': circles,
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

                return results["circles"]
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
    Evaluate the program by running it once and checking the sum of radii.
    The returned dictionary conforms to the new specified structure.

    Args:
        program_path: Path to the program file

    Returns:
        A dictionary with 'status', 'summary', 'score', 'metrics', and 'artifacts'.
    """
    # Target value from the paper
    TARGET_VALUE = 2.365  # AlphaEvolve result for n=21
    timeout_duration = 3600
    status = "success"

    try:
        start_time = time.time()

        # Use subprocess to run with timeout
        circles = run_with_timeout(
            program_path, timeout_seconds=timeout_duration
        )

        end_time = time.time()
        eval_time = end_time - start_time

        # Ensure centers and radii are numpy arrays
        if not isinstance(circles, np.ndarray):
            circles = np.array(circles)

        # Check shape and size
        shape_valid = circles.shape == (21, 3)
        if not shape_valid:
            shape_error = f"Invalid shapes: circles={circles.shape}, expected (21, 3)"
            print(shape_error)

            return {
                "status": "validation_failed",
                "summary": "Validation failed: The output 'centers' array has an incorrect shape.",
                "score": 0.0,
                "metrics": {
                    "sum_radii": 0.0,
                    "target_ratio": 0.0,
                    "validity": 0.0,
                    "eval_time": float(eval_time),
                },
                "artifacts": {
                    "stderr": shape_error,
                    "failure_stage": "shape_validation",
                    "expected_shapes": "centers: (21, 2)",
                    "actual_shapes": f"centers: {circles.shape}",
                    "execution_time": f"{eval_time:.2f}s",
                },
            }

        # Validate solution
        is_valid, validation_details = validate_packing(circles)

        # Calculate sum
        sum_radii = float(np.sum(circles[:, 2])) if is_valid else 0.0

        # Target ratio (how close we are to the target)
        target_ratio = sum_radii / TARGET_VALUE if is_valid else 0.0

        # Validity score
        validity = 1.0 if is_valid else 0.0

        # Combined score - higher is better
        combined_score = target_ratio * validity

        print(
            f"Evaluation: valid={is_valid}, sum_radii={sum_radii:.6f}, "
            f"target={TARGET_VALUE}, ratio={target_ratio:.6f}, time={eval_time:.2f}s"
        )

        # Prepare artifacts with packing details
        artifacts = {
            "execution_time": f"{eval_time:.2f}s",
            "packing_summary": f"Sum of radii: {sum_radii:.6f}/{TARGET_VALUE} = {target_ratio:.4f}",
            "validation_report": f"Valid: {is_valid}, Violations: {len(validation_details.get('overlaps_check', []))} overlaps, Perimeter of minimum circumscribing rectangle: {validation_details.get('perimeter'):.6f}",
        }
        summary = f"Evaluation successful. The packing is valid with a total radii sum of {sum_radii:.6f}."

        # Add validation details if there are issues
        if not is_valid:
            summary = f"Validation failed: {validation_details['error_message']}"

            if validation_details.get("overlaps_check"):
                artifacts["overlaps_check"] = "\n".join(
                    validation_details["overlaps_check"]
                )
            if validation_details.get("perimeter_check"):
                artifacts["perimeter_check"] = "\n".join(validation_details["perimeter_check"])
            artifacts["failure_stage"] = "geometric_validation"

            # Add successful packing stats for good solutions
            if is_valid and target_ratio > 0.95:  # Near-optimal solutions
                artifacts["stdout"] = (
                    f"Excellent packing! Achieved {target_ratio:.1%} of target value"
                )
                min_radius = float(validation_details['min_radius'])
                max_radius = float(validation_details['max_radius'])
                avg_radius = float(validation_details['avg_radius'])
                artifacts["radius_stats"] = (
                    f"Min: {min_radius:.6f}, Max: {max_radius:.6f}, Avg: {avg_radius:.6f}"
                )

        return {
            "status": status,
            "summary": summary,
            "score": float(combined_score),
            "metrics": {
                "sum_radii": float(sum_radii),
                "target_ratio": float(target_ratio),
                "validity": float(validity),
                "eval_time": float(eval_time),
            },
            "artifacts": artifacts,
        }

    except TimeoutError as e:
        error_msg = f"Evaluation timed out: {str(e)}"
        print(error_msg)
        return {
            "status": "execution_failed",
            "summary": f"Execution failed: The program timed out after {timeout_duration} seconds.",
            "score": 0.0,
            "metrics": {
                "sum_radii": 0.0,
                "target_ratio": 0.0,
                "validity": 0.0,
                "eval_time": float(timeout_duration),
            },
            "artifacts": {
                "stderr": error_msg,
                "failure_stage": "execution_timeout",
                "timeout_duration": f"{timeout_duration}s",
                "suggestion": "Consider optimizing the packing algorithm for faster convergence",
            },
        }
    except Exception as e:
        error_msg = f"Program execution failed: {str(e)}"
        print(error_msg, file=sys.stderr)
        traceback.print_exc()
        return {
            "status": "execution_failed",
            "score": 0.0,
            "summary": error_msg,
            "artifacts": {
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
            },
        }


if __name__ == "__main__":
    file = "./best_solution.py"
    res = evaluate(file)
    print(f"{res}")