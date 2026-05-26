import os

import pandas as pd

from BLRun.runner import Runner


class XGBRunner(Runner):
    """Concrete runner for the PIDC GRN inference algorithm."""

    def generateInputs(self):
        """
        Function to generate desired outputs for XGBDENSE.
        If the folder/files under RunnerObj.datadir exist,
        this function will not do anything.
        """
        LGB_EXPRESSION_FILE = self.working_dir / "ExpressionData.csv"
        input_file = self.input_dir / self.exprData
        if not LGB_EXPRESSION_FILE.exists():
            import shutil

            shutil.copy(
                input_file,
                LGB_EXPRESSION_FILE,
            )
        self.inputPath = LGB_EXPRESSION_FILE
        self.outFile = f"{self.working_dir}/outFile.txt"
        self.statsPath = str(self.working_dir) + "/outStats.json"
        self.timePath = str(self.working_dir) + "/time.txt"

    def run(self):
        # TODO::
        cmdToRun = " ".join(
            [
                "time -v -o",
                f"{self.timePath}",
                "python -m gbr.cli csv --device=cpu --method=xgb",
                f"--out_file {self.outFile}",
                f"--rstats_out_file {self.statsPath}",
                f"--csv_file {self.inputPath}",
            ]
        )
        print(cmdToRun)
        os.system(cmdToRun)

    def parseOutput(self) -> None:
        # Quit if output file does not exist
        outFile = self.working_dir / "outFile.txt"
        if not outFile.exists():
            print(str(outFile) + " does not exist, skipping...")
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
        self._write_ranked_edges(final_df)
