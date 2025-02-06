import pyhop
import json

def check_enough(state, ID, item, num):
    if getattr(state, item)[ID] >= num:
        return []
    return False

def produce_enough(state, ID, item, num):
    return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods('have_enough', check_enough, produce_enough)

def produce(state, ID, item):
    return [('produce_{}'.format(item), ID)]

pyhop.declare_methods('produce', produce)

def make_method(name, rule):
    """
    Create an HTN method for crafting.
    """
    def method(state, ID):
        subtasks = []

        # Ensure all required tools exist
        if "Requires" in rule:
            for item, quantity in rule["Requires"].items():
                subtasks.append(('have_enough', ID, item, quantity))

        # Ensure all required materials exist
        if "Consumes" in rule:
            for item, quantity in rule["Consumes"].items():
                subtasks.append(('have_enough', ID, item, quantity))

        # Add the crafting operation
        subtasks.append(("op_" + name.replace(" ", "_"), ID))

        return subtasks

    return method


def declare_methods(data):
    for recipe_name, rule in data["Recipes"].items():
        method_name = "produce_" + recipe_name.split(" ")[-1]  # Extract item name
        method = make_method(recipe_name, rule)
        method.__name__ = method_name

        if method_name in pyhop.methods:
            pyhop.methods[method_name].append(method)
        else:
            pyhop.declare_methods(method_name, method)


def make_operator(rule):
    def operator(state, ID):
        # Check if required tools exist
        if "Requires" in rule:
            for item, quantity in rule["Requires"].items():
                if getattr(state, item)[ID] < quantity:
                    return False  # Not enough resources

        # Check if required consumable materials exist
        if "Consumes" in rule:
            for item, quantity in rule["Consumes"].items():
                if getattr(state, item)[ID] < quantity:
                    return False  # Not enough materials to consume

        # Apply changes
        if "Consumes" in rule:
            for item, quantity in rule["Consumes"].items():
                getattr(state, item)[ID] -= quantity

        if "Produces" in rule:
            for item, quantity in rule["Produces"].items():
                getattr(state, item)[ID] += quantity

        if "Time" in rule:
            if state.time[ID] < rule["Time"]:
                return False  # Not enough time
            state.time[ID] -= rule["Time"]

        return state

    return operator


def declare_operators(data):
    operators = []
    for recipe_name, rule in data["Recipes"].items():
        op_name = "op_" + recipe_name.replace(" ", "_")  # Format name
        operator = make_operator(rule)
        operator.__name__ = op_name
        operators.append(operator)

    pyhop.declare_operators(*operators)


def add_heuristic(data, ID):
    def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
        # Prevent redundant crafting of tools
        if curr_task[0].startswith("produce_") and state.time[ID] <= 0:
            return True  # Stop this branch, no time left

        # Avoid recursive loops where the same item is produced repeatedly
        if curr_task in calling_stack:
            return True  # Prevent cycles

        return False

    pyhop.add_check(heuristic)


def set_up_state(data, ID, time=0):
    state = pyhop.State('state')
    state.time = {ID: time}

    for item in data['Items'] + data['Tools']:
        setattr(state, item, {ID: 0})

    for item, num in data['Initial'].items():
        setattr(state, item, {ID: num})

    return state

def set_up_goals(data, ID):
    goals = []
    for item, num in data['Goal'].items():
        goals.append(('have_enough', ID, item, num))

    return goals

if __name__ == '__main__':
	rules_filename = 'crafting.json'
	
	with open(rules_filename) as f:
		data = json.load(f)
	
	# # Test case #1
	# state = set_up_state(data, 'agent', time=0)
	# state.plank = {'agent': 1}
	# goals = [('have_enough', 'agent', 'plank', 1)]
	
	# Test case #2
	state = set_up_state(data, 'agent', time=300)
	goals = [('have_enough', 'agent', 'plank', 1)]
	
	# # Test case #3
	# state = set_up_state(data, 'agent', time=10)
	# goals = [('have_enough', 'agent', 'wooden_pickaxe', 1)]
	
	# # Test case #4
	# state = set_up_state(data, 'agent', time=100)
	# goals = [('have_enough', 'agent', 'iron_pickaxe', 1)]
	
	# # Test case #5
	# goals = set_up_state(data, 'agent', time=175)
	# state = [('have_enough', 'agent', 'cart', 1), ('have_enough', 'agent', 'rail', 10)]
	
	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')
	
	# pyhop.print_operators()
	# pyhop.print_methods()
	
	# Hint: verbose output can take a long time even if the solution is correct; 
	# try verbose=1 if it is taking too long
	pyhop.pyhop(state, goals, verbose=3)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)
