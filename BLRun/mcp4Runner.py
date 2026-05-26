import os

import pandas as pd

from BLRun.runner import Runner


class MCP4Runner(Runner):
    """Concrete runner for the MCP4 GRN inference algorithm."""

    def generateInputs(self):
        """
        Function to generate desired inputs for MCP4.
        If the folder/files under self.input_dir exist,
        this function will not do anything.
        """
        # Create ExpressionData.csv file in the created input directory
        MCP4_EXPRESSION_FILE = self.working_dir / "ExpressionData.csv"
        input_file = self.input_dir / self.exprData
        if not MCP4_EXPRESSION_FILE.exists():
            import shutil

            shutil.copy(
                input_file,
                MCP4_EXPRESSION_FILE,
            )

        self.inputPath = MCP4_EXPRESSION_FILE
        self.outFilePrefix = f"{self.working_dir}/outFile"
        self.miFile = f"{self.working_dir}/miFile.h5"
        self.statsPath = str(self.working_dir) + "/outStats.json"
        self.timePath = str(self.working_dir) + "/time.txt"

    def run(self):
        """
        Function to run MCP4 algorithm
        """
        # TODO::
        cmdToRun = " ".join(
            [
                "time -v -o",
                f"{self.timePath}",
                ' /bin/sh -c " mcpnet/build/bin/mi ',
                f"-i {self.inputPath}",
                f"-o {self.miFile}",
                ";",
                "mcpnet/build/bin/mcpnet ",
                f"-i {self.miFile}",
                " --mi-input -m 1 2 3 ",
                f'-o {self.outFilePrefix} "',
            ]
        )
        print(cmdToRun)
        os.system(cmdToRun)

        pass

    def parseOutput(self):
        """
        Function to parse outputs from MCP4.
        """

        # Read output
        dfx = pd.read_hdf(f"{self.outFilePrefix}_inmi.mcp4.h5")
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
