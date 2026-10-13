
"""
Educational Bayesian probability model for the
Healthcare AI case study.

Uses illustrative probabilities only; it is not a
clinically validated diagnostic model.
"""

def calculate_probability(prior, sensitivity, specificity, positive=True):
    """
    Calculate a posterior probability using Bayes' theorem.

    prior: assumed prior probability between 0 and 1
    sensitivity: assumed sensitivity between 0 and 1
    specificity: assumed specificity between 0 and 1
    positive: True for a positive test, False for a negative test
    """
    values = [prior, sensitivity, specificity]

    if any(not isinstance(x, (int, float)) or isinstance(x, bool)
           or not 0 <= x <= 1 for x in values):
        raise ValueError("All probabilities must be between 0 and 1.")

    if positive:
        numerator = sensitivity * prior
        denominator = numerator + (1 - specificity) * (1 - prior)
    else:
        numerator = (1 - sensitivity) * prior
        denominator = numerator + specificity * (1 - prior)

    if denominator == 0:
        raise ValueError("Posterior probability is undefined for these inputs.")

    return numerator / denominator


def uncertainty_label(probability):
    """Describe the model's probability level, not clinical urgency."""
    if not 0 <= probability <= 1:
        raise ValueError("Probability must be between 0 and 1.")

    if probability < 0.30:
        return "Lower estimated probability"
    elif probability < 0.70:
        return "Intermediate estimated probability"
    return "Higher estimated probability"


if __name__ == "__main__":
    # Illustrative example only; not real patient data.
    posterior = calculate_probability(
        prior=0.10,
        sensitivity=0.80,
        specificity=0.90,
        positive=True
    )

    print(f"Illustrative posterior probability: {posterior:.2%}")
    print(f"Probability category: {uncertainty_label(posterior)}")
