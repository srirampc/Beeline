import os
import pandas as pd

from BLRun.runner import Runner


class PIDCRunner(Runner):
    """Concrete runner for the PIDC GRN inference algorithm."""

    def generateInputs(self):
        '''
        Function to generate desired inputs for PIDC.
        If the folder/files under self.input_dir exist,
        this function will not do anything.
        '''

        # Create ExpressionData.csv file in the created input directory
        PIDC_EXPRESSION_FILE = self.working_dir / "ExpressionData.csv"
        if not PIDC_EXPRESSION_FILE.exists():
            ExpressionData = pd.read_csv(self.input_dir / self.exprData,
                                         header = 0, index_col = 0)
            ExpressionData.to_csv(PIDC_EXPRESSION_FILE,
                                 sep = '\t', header  = True, index = True)
        self.inputPath = PIDC_EXPRESSION_FILE
        self.outFile = f"{self.working_dir}/outFile.txt"

    def run(self):
        '''
        Function to run PIDC algorithm
        '''

        timePath = str(self.working_dir) + '/time.txt'
        cmdToRun = ' '.join([
            'time -v -o',
            timePath,
            'julia Algorithms/PIDC/runPIDC.jl',
            str(self.inputPath),
            self.outFile,
        ])

        self._run_docker(cmdToRun)

    def parseOutput(self):
        '''
        Function to parse outputs from PIDC.
        '''
        workDir = self.working_dir
        outFile = workDir / 'outFile.txt'

        # Quit if output file does not exist
        if not outFile.exists():
            print(str(outFile) + ' does not exist, skipping...')
            return

        # Read output (headerless: col 0 = Gene1, col 1 = Gene2, col 2 = EdgeWeight)
        OutDF = pd.read_csv(outFile, sep = '\t', header = None)

        self._write_ranked_edges(pd.DataFrame({
            'Gene1':      OutDF[0],
            'Gene2':      OutDF[1],
            'EdgeWeight': OutDF[2],
        }))
