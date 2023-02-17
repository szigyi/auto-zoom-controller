

def calculate_number_of_turns(number_of_total_turns, interval_in_seconds, length_in_minutes):
	length_in_seconds = length_in_minutes * 60
	number_of_activations = length_in_seconds / interval_in_seconds
	return int(round(number_of_total_turns / number_of_activations, 0))


def calculate_number_of_activations(interval_in_seconds, length_in_minutes):
	length_in_seconds = length_in_minutes * 60
	return length_in_seconds / interval_in_seconds
