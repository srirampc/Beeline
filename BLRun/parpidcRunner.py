import os

import pandas as pd

from BLRun.runner import Runner

CFG_TEMPLATE = """h5ad_file: {h5ad}
hist_data_file: {hist}
misi_data_file: {misi}
puc_file: {puc}
pidc_file: {pidc}
#
nrounds: 0
nsamples: 0
nobs: 0
nvars: 0
mode:
  - hist_nodes
  - hist2misi_dist
  - puc_lmr_dist
  - puc2pidc
tbase: "2"
save_nodes: False
save_node_pairs: True
lmr_only: True
"""


class ParPIDCRunner(Runner):
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
        self.inputh5ad = self.working_dir / "ExpressionData.h5ad"
        self.hist = self.working_dir / "hist.h5"
        self.misi = self.working_dir / "misi.h5"
        self.puc = self.working_dir / "puc.h5"
        # self.pidc = self.working_dir / "pidc.h5"
        self.config = self.working_dir / "config.yaml"
        self.outFile = f"{self.working_dir}/outFile.h5"
        #
        import anndata as an
        import pandas as pd
        df = pd.read_csv(self.inputPath, index_col=0)
        vdf = pd.DataFrame({'gene_ids': df.index.to_list()}, index=df.index)
        odf = pd.DataFrame({'sample_id': df.columns}, index=df.columns)
        adx = an.AnnData(X=df.to_numpy().T, var=vdf, obs=odf)
        adx.write_h5ad(self.inputh5ad)
        #
        config_text = CFG_TEMPLATE.format(
            h5ad=self.inputh5ad,
            hist=self.hist,
            misi=self.misi,
            puc=self.puc,
            pidc=self.outFile,
        )
        with open(self.config, "w") as ofhandle:
            ofhandle.write(config_text)
        #
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
                ' /bin/sh -c ',
                '"mpirun -np 2 parensnet_rs/target/release/pucgrn_cli ',
                f' {self.config}"',
            ]
        )
        print(cmdToRun)
        os.system(cmdToRun)

    def parseOutput(self):
        """
        Function to parse outputs from MI.
        """
        # Read output
        import h5py
        import anndata as an
        adx = an.read_h5ad(self.inputh5ad)
        with h5py.File(self.outFile) as fx:
            idx = fx["data/index"][:]  # pyright: ignore[reportIndexIssue]
            pidc = fx["data/pidc"][:]  # pyright: ignore[reportIndexIssue]
        pidc_df = pd.DataFrame(
            {'s': idx[:, 0], 't': idx[:, 1], 'pidc': pidc}  # pyright: ignore[reportIndexIssue]
        )
        gene_ids = adx.var.index.to_list()
        gene_df = pd.DataFrame({
                'gene': gene_ids,
                'id': range(0, len(gene_ids))
        })
        mdf = pidc_df.merge(
            gene_df, left_on='s', right_on='id'
        ).merge(gene_df, left_on='t', right_on='id', suffixes=('_s', '_t'))
        OutDF: pd.DataFrame = mdf[['gene_s', 'gene_t', 'pidc']]  # pyright: ignore[reportAssignmentType]
        OutDF = OutDF[OutDF["gene_s"] != OutDF["gene_t"]]  # pyright: ignore[reportAssignmentType]
        RevDF = OutDF.rename(
            columns={
                "gene_s": "gene_t",
                "gene_t": "gene_s",
                "pidc": "pidc",
            }
        )
        OutDF = pd.concat([OutDF, RevDF])
        OutDF = OutDF.sort_values(by=["pidc"], ascending=False)

        OutDF = OutDF.rename(
            columns={
                "gene_s": "Gene1",
                "gene_t": "Gene2",
                "pidc": "EdgeWeight",
            }
        )
        # outFile = workDir / 'outFile.txt'
        # outPath = outDir + "rankedEdges.csv"
        # final_df.to_csv(outPath, sep="\t", index=False)
        self._write_ranked_edges(OutDF)
