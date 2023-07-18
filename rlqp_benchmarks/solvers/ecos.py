import cvxpy.settings as stgs
import cvxpy
from . import statuses as s
from .results import Results
from rlqp_benchmarks.utils.general import is_qp_solution_optimal


class ECOSSolver(object):

    STATUS_MAP = {stgs.OPTIMAL: s.OPTIMAL,
                  stgs.OPTIMAL_INACCURATE: s.OPTIMAL_INACCURATE,
                  stgs.INFEASIBLE: s.PRIMAL_INFEASIBLE,
                  stgs.INFEASIBLE_INACCURATE: s.PRIMAL_INFEASIBLE_INACCURATE,
                  stgs.UNBOUNDED_INACCURATE: s.DUAL_INFEASIBLE_INACCURATE}

    def __init__(self, settings={}):
        '''
        Initialize solver object by setting require settings
        '''
        self._settings = settings

    def name(self):
        return 'ECOS'

    @property
    def settings(self):
        """Solver settings"""
        return self._settings

    def solve(self, example):
        '''
        Solve problem

        Args:
            example: example object

        Returns:
            Results structure
        '''
        problem = example.cvxpy_problem

        if 'verbose' in self._settings:
            verbose = self._settings["verbose"]
        else:
            verbose = False

        try:
            obj_val = problem.solve(solver=cvxpy.ECOS, verbose=verbose)
        except cvxpy.SolverError:
            if 'verbose' in self._settings:  # if verbose is null, suppress it
                if self._settings['verbose']:
                    print("Error in ECOS solution\n")
            return Results(s.SOLVER_ERROR, None, None, None,
                           None, None)

        status = self.STATUS_MAP.get(problem.status, s.SOLVER_ERROR)

        # Obtain time and number of iterations
        run_time = problem.solver_stats.solve_time \
            + problem.solver_stats.setup_time

        niter = problem.solver_stats.num_iters

        # Get primal, dual solution
        x, y = example.revert_cvxpy_solution()

        # Validate status
        if not is_qp_solution_optimal(example.qp_problem, x, y,
                                      high_accuracy=self._settings.get('high_accuracy')):
            status = s.SOLVER_ERROR

        # Validate execution time
        if 'time_limit' in self._settings:
            if run_time > self._settings['time_limit']:
                status = s.TIME_LIMIT

        return Results(status,
                       obj_val,
                       x,
                       y,
                       run_time,
                       niter)
