import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):
        modified_domains = {}
        assigned_vars = [v for v in self.network.variables if v.isAssigned()]

        for av in assigned_vars:
            val = av.getAssignment()
            for neighbor in self.network.getNeighborsOfVariable(av):
                if (not neighbor.isAssigned()) and neighbor.getDomain().contains(val):
                    self.trail.push(neighbor)
                    neighbor.removeValueFromDomain(val)
                    modified_domains[neighbor] = list(neighbor.getDomain().values)

                    if neighbor.getDomain().isEmpty():
                        return (modified_domains, False)

        return (modified_domains, True)
    # =================================================================
    # Arc Consistency
    # =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
                that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        assigned_vars = {}  # var -> value assigned during propagation

        changed = True
        while changed:
            changed = False

            # Forward-checking pruning
            fc_mods, ok = self.forwardChecking()
            if not ok:
                return (assigned_vars, False)

            # Only-choice: for each constraint, if a value can only go in one var, assign it
            for c in self.network.getConstraints():
                scope = c.vars  # consistent with your arcConsistency usage

                # collect possible values in this constraint among unassigned vars
                possible_vals = set()
                for var in scope:
                    if not var.isAssigned():
                        possible_vals.update(var.getDomain().values)

                for val in possible_vals:
                    candidates = []
                    for var in scope:
                        if (not var.isAssigned()) and var.getDomain().contains(val):
                            candidates.append(var)

                    if len(candidates) == 0:
                        # no place for this value in this unit => inconsistent
                        return (assigned_vars, False)

                    if len(candidates) == 1:
                        only_var = candidates[0]
                        self.trail.push(only_var)
                        only_var.assignValue(val)
                        assigned_vars[only_var] = val
                        changed = True

                        if not self.assignmentsCheck():
                            return (assigned_vars, False)

        return (assigned_vars, True)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return False

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        unassigned = [v for v in self.network.variables if not v.isAssigned()]
        if not unassigned:
            return None
        return min(unassigned, key=lambda v: v.getDomain().size())

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        unassigned = [v for v in self.network.variables if not v.isAssigned()]
        if not unassigned:
            return [None]

        min_size = min(v.getDomain().size() for v in unassigned)
        mrv_vars = [v for v in unassigned if v.getDomain().size() == min_size]

        if len(mrv_vars) == 1:
          return mrv_vars

        def degree(var):
            return sum(1 for n in self.network.getNeighborsOfVariable(var) if not n.isAssigned())

        max_deg = max(degree(v) for v in mrv_vars)
        tied = [v for v in mrv_vars if degree(v) == max_deg]
        return tied

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        return sorted(list(v.getDomain().values))

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        values = list(v.getDomain().values)

        def elim_count(val):
            count = 0
            for n in self.network.getNeighborsOfVariable(v):
                if not n.isAssigned() and n.getDomain().contains(val):
                    count += 1
            return count

        return sorted(values, key=elim_count)

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)
