import os
import pandas as pd

from BLRun.runner import Runner


class GENIE3Runner(Runner):
    """Concrete runner for the GENIE3 GRN inference algorithm."""

    def generateInputs(self):
        '''
        Function to generate desired inputs for GENIE3.
        If the folder/files under self.input_dir exist,
        this function will not do anything.
        '''

        # Create ExpressionData.csv file in the created input directory
        GENIE3_EXPRESSION_FILE = self.working_dir / "ExpressionData.csv"
        if not GENIE3_EXPRESSION_FILE.exists():
            # input data
            ExpressionData = pd.read_csv(self.input_dir / self.exprData,
                                         header = 0, index_col = 0)

            # Write .csv file — arboreto expects cells as rows, genes as columns
            ExpressionData.T.to_csv(GENIE3_EXPRESSION_FILE,
                                 sep = '\t', header  = True, index = True)
        self.inputPath = GENIE3_EXPRESSION_FILE
        self.outFile = f"{self.working_dir}/outFile.txt"

    def run(self):
        '''
        Function to run GENIE3 algorithm
        '''

        timePath = str(self.working_dir) + '/time.txt'
        cmdToRun = ' '.join([
            'time -v -o',
            timePath,
            'python runArboreto.py --algo=GENIE3',
            f"--inFile={str(self.inputPath)} ",
            f"--outFile={self.outFile}"
        ])

        self._run_docker(cmdToRun)

    def parseOutput(self):
        '''
        Function to parse outputs from GENIE3.
        '''
        workDir = self.working_dir
        outFile = workDir / 'outFile.txt'

        # Quit if output file does not exist
        if not outFile.exists():
            print(str(outFile) + ' does not exist, skipping...')
            return

        # Read output
        OutDF = pd.read_csv(outFile, sep = '\t', header = 0)

        self._write_ranked_edges(OutDF.rename(columns={
            'TF': 'Gene1', 'target': 'Gene2', 'importance': 'EdgeWeight'
        })[['Gene1', 'Gene2', 'EdgeWeight']])
