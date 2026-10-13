"""
Expected utility decision support for the Healthcare AI case study.

Illustrative educational model only. Not for clinical use.
"""

def calculate_expected_utility(outcomes):
    """
    outcomes: list of (probability, utility) pairs.
    Returns the sum of probability * utility.
    """
    if not outcomes:
        raise ValueError("At least one outcome is required.")

    for probability, utility in outcomes:
        if not 0 <= probability <= 1:
            raise ValueError("Probabilities must be between 0 and 1.")

    total_probability = sum(p for p, _ in outcomes)
    if abs(total_probability - 1.0) > 1e-6:
        raise ValueError("Outcome probabilities must sum to 1.")

    return sum(probability * utility for probability, utility in outcomes)


def choose_best_action(actions):
    """
    actions: dictionary mapping action names to outcome lists.
    Returns each action's expected utility and the highest-utility action.
    """
    if not actions:
        raise ValueError("At least one action is required.")

    scores = {
        action: calculate_expected_utility(outcomes)
        for action, outcomes in actions.items()
    }

    best_action = max(scores, key=scores.get)
    return best_action, scores


if __name__ == "__main__":
    # Illustrative utilities, not medical recommendations.
    actions = {
        "Routine follow-up": [(0.8, 10), (0.2, -20)],
        "Clinical assessment": [(0.9, 8), (0.1, -5)],
        "Urgent clinical review": [(0.95, 6), (0.05, -2)],
    }

    best_action, scores = choose_best_action(actions)

    print("Illustrative expected utility scores:")
    for action, score in scores.items():
        print(f"{action}: {score:.2f}")

    print(f"\nHighest-utility action in this example: {best_action}")
    print("These scores are hypothetical and must not guide real patient care.")
