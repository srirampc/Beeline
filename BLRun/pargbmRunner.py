import os

import pandas as pd

from BLRun.runner import Runner

CFG_TEMPLATE = """h5ad_file: {h5ad}
tf_csv_file: {tfcsv}
output_file: {gbgrn}
#
nroundup: 3
mode: gb_grn
gbm_params:
  verbose: 0
  num_threads: 4
n_sample_genes: {samples}
"""


class ParGBMRunner(Runner):
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
        self.tfcsv = self.working_dir / "tf.csv"
        self.config = self.working_dir / "config.yaml"
        self.outFile = f"{self.working_dir}/outFile.h5"
        #
        import anndata as an
        import pandas as pd
        df = pd.read_csv(self.inputPath, index_col=0)
        gene_ids = df.index.to_list()
        vdf = pd.DataFrame({'gene_ids': gene_ids}, index=df.index)
        odf = pd.DataFrame({'sample_id': df.columns}, index=df.columns)
        adx = an.AnnData(X=df.to_numpy().T, var=vdf, obs=odf)
        adx.write_h5ad(self.inputh5ad)
        #
        gdf = pd.DataFrame({'gene': gene_ids})
        gdf.to_csv(self.tfcsv, index=False)
        #
        config_text = CFG_TEMPLATE.format(
            h5ad=self.inputh5ad,
            tfcsv=self.tfcsv,
            gbgrn=self.outFile,
            samples=int(len(gene_ids)/2),
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
                '"mpirun -np 1 parensnet_rs/target/release/gbgrn_cli ',
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
        with h5py.File(self.outFile) as hfx:
            gb_df = pd.DataFrame(hfx['gbnet/data'][:])  # pyright: ignore[reportIndexIssue] 
            tf_lst = [x.decode('utf-8') for x in hfx['gbnet']['tf'][:]]  # pyright: ignore[reportIndexIssue] 
            tgt_lst = [x.decode('utf-8') for x in hfx['gbnet']['target'][:]]  # pyright: ignore[reportIndexIssue] 
        tf_df = pd.DataFrame({
                'tf_gene': tf_lst,
                'id': range(0, len(tf_lst))
        })
        tgt_df = pd.DataFrame({
                'target_gene': tgt_lst,
                'id': range(0, len(tgt_lst))
        })
        mdf = gb_df.merge(
            tf_df, left_on='tf', right_on='id'
        ).merge(tgt_df, left_on='target', right_on='id')
        OutDF: pd.DataFrame = mdf[['tf_gene', 'target_gene', 'importance']]  # pyright: ignore[reportAssignmentType]
        OutDF = OutDF[OutDF["tf_gene"] != OutDF["target_gene"]]  # pyright: ignore[reportAssignmentType]
        # RevDF = OutDF.rename(
        #     columns={
        #         "tf_gene": "target_gene",
        #         "target_gene": "tf_gene",
        #         "importance": "importance",
        #     }
        # )
        # OutDF = pd.concat([OutDF, RevDF])
        OutDF = OutDF.sort_values(by=["importance"], ascending=False)

        OutDF = OutDF.rename(
            columns={
                "tf_gene": "Gene1",
                "target_gene": "Gene2",
                "importance": "EdgeWeight",
            }
        )
        # outFile = workDir / 'outFile.txt'
        # outPath = outDir + "rankedEdges.csv"
        # final_df.to_csv(outPath, sep="\t", index=False)
        self._write_ranked_edges(OutDF)
