import os

import pandas as pd

from BLRun.runner import Runner


class MIRunner(Runner):
    """Concrete runner for the MI GRN inference algorithm."""

    def generateInputs(self):
        """
        Function to generate desired inputs for MI.
        If the folder/files under self.input_dir exist,
        this function will not do anything.
        """
        # Create ExpressionData.csv file in the created input directory
        MI_EXPRESSION_FILE = self.working_dir / "ExpressionData.csv"
        input_file = self.input_dir / self.exprData
        if not MI_EXPRESSION_FILE.exists():
            import shutil

            shutil.copy(
                input_file,
                MI_EXPRESSION_FILE,
            )

        self.inputPath = MI_EXPRESSION_FILE
        self.outFile = f"{self.working_dir}/outFile.h5"
        self.statsPath = str(self.working_dir) + "/outStats.json"
        self.timePath = str(self.working_dir) + "/time.txt"

    def run(self):
        """
        Function to run MI algorithm
        """
        # TODO::
        cmdToRun = " ".join(
            [
                "time -v -o",
                f"{self.timePath}",
                ' /bin/sh -c " mcpnet/build/bin/mi ',
                f"-i {self.inputPath}",
                f'-o {self.outFile} "',
            ]
        )
        print(cmdToRun)
        os.system(cmdToRun)

    def parseOutput(self):
        """
        Function to parse outputs from MI.
        """
        # Read output
        dfx = pd.read_hdf(self.outFile)
        OutDF = (
            dfx.transpose()  # pyright: ignore[reportAttributeAccessIssue]
            .stack()
            .reset_index()
            .set_axis(["TF", "target", "importance"], axis=1)
        )
        OutDF = OutDF[OutDF["TF"] != OutDF["target"]]
        OutDF = OutDF.sort_values(by=["importance"], ascending=False)

        OutDF = OutDF.rename(
            columns={
                "TF": "Gene1",
                "target": "Gene2",
                "importance": "EdgeWeight",
            }
        )
        # outFile = workDir / 'outFile.txt'
        # outPath = outDir + "rankedEdges.csv"
        # final_df.to_csv(outPath, sep="\t", index=False)
        self._write_ranked_edges(OutDF)
