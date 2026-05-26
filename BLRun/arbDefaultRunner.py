import os

import pandas as pd

from BLRun.runner import Runner


class ARBDefaultRunner(Runner):
    def generateInputs(self):
        """
        Function to generate desired outputs for ARBDEF.
        If the folder/files under RunnerObj.datadir exist,
        this function will not do anything.
        """
        ARB_EXPRESSION_FILE = self.working_dir / "ExpressionData.csv"
        input_file = self.input_dir / self.exprData
        if not ARB_EXPRESSION_FILE.exists():
            import shutil

            shutil.copy(
                input_file,
                ARB_EXPRESSION_FILE,
            )

        self.inputPath = ARB_EXPRESSION_FILE
        self.outFile = f"{self.working_dir}/outFile.txt"
        self.statsPath = str(self.working_dir) + "/outStats.json"
        self.timePath = str(self.working_dir) + "/time.txt"

    def run(self):
        """
        Function to run ARB Default algorithm
        """
        cmdToRun = " ".join(
            [
                "time -v -o",
                f"{self.timePath}",
                "python -m gbr.cli csv --method=arb:default",
                f"--out_file {self.outFile}",
                f"--rstats_out_file {self.statsPath}",
                f"--csv_file {self.inputPath}",
            ]
        )
        self._run_docker(cmdToRun)

    def parseOutput(self):
        """
        Function to parse outputs from ARBDEF.
        """
        # Quit if output file does not exist
        outFile = self.working_dir / "outFile.txt"
        if not outFile.exists():
            print(str(outFile) + ' does not exist, skipping...')
            return
        # Read output
        OutDF: pd.DataFrame = pd.read_csv(self.outFile, header=0, index_col=0)

        final_df = OutDF.rename(
            columns={
                "TF": "Gene1",
                "target": "Gene2",
                "importance": "EdgeWeight",
            }
        )
        self._write_ranked_edges(
            final_df,
        )
