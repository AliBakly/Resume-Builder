import os
import sys
import argparse
import itertools
from pathlib import Path
import subprocess
import shutil


class ResumeBuilder:
    def __init__(self, mode, pdf_name, min_projects, max_projects):
        """
        mode: 'combinations' or 'permutations'
        pdf_name: The name of the PDF (e.g. 'AliBakly.pdf') saved in each folder
        min_projects: Minimum number of projects in each resume
        max_projects: Maximum number of projects in each resume
        """
        self.mode = mode
        self.pdf_name = pdf_name
        self.min_projects = min_projects
        self.max_projects = max_projects

        self.base_dir = Path(os.getcwd())
        self.projects_dir = self.base_dir / "projects"
        self.output_dir = self.base_dir / "output"
        self.template_file = self.base_dir / "template.tex"

    def setup_directories(self):
        """Create the projects/ and output/ directories if needed."""
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def read_project(self, project_file):
        """Read text from a .tex file in projects/."""
        with open(self.projects_dir / f"{project_file}.tex", 'r', encoding='utf-8') as f:
            return f.read()

    def build_pdf(self, projects, folder_name):
        """
        1) Create a folder named folder_name inside output/.
        2) Insert each project's .tex text into the template (placeholder '%PROJECT_CONTENT%').
        3) Compile pdflatex -> single PDF named self.pdf_name in that folder.
        """
        # Read the main template
        with open(self.template_file, 'r', encoding='utf-8') as tf:
            template = tf.read()

        # Merge project .tex contents
        project_texts = [self.read_project(p) for p in projects]
        merged_text = "\n".join(project_texts)

        # Replace placeholder
        content = template.replace("%PROJECT_CONTENT%", merged_text)

        # Folder for this resume
        out_folder = self.output_dir / folder_name
        os.makedirs(out_folder, exist_ok=True)

        # Write a temporary .tex
        temp_tex = out_folder / "temp.tex"
        with open(temp_tex, 'w', encoding='utf-8') as f:
            f.write(content)

        # Run pdflatex in out_folder
        subprocess.run([
            "pdflatex",
            "-output-directory", str(out_folder),
            str(temp_tex)
        ], check=True)

        # Clean up temp files
        for ext in (".aux", ".log", ".out", ".toc", ".tex"):
            tmp = out_folder / f"temp{ext}"
            if tmp.exists():
                tmp.unlink()

        # Move/rename the PDF from temp.pdf -> pdf_name
        temp_pdf = out_folder / "temp.pdf"
        final_pdf = out_folder / self.pdf_name
        if temp_pdf.exists():
            shutil.move(str(temp_pdf), str(final_pdf))

    def run(self):
        """
        Generate subfolders with one PDF in each, depending on the requested mode.
        Loop through user-defined subset sizes.
        """
        self.setup_directories()
        # Gather list of all project files, minus the .tex extension
        project_files = [f.stem for f in self.projects_dir.glob("*.tex")]

        # Check if projects folder is empty
        if not project_files:
            raise ValueError("The 'projects/' folder is empty. Please add at least one .tex file to generate resumes.")

        # Validate subset size bounds
        total_projects = len(project_files)
        if not (1 <= self.min_projects <= total_projects):
            raise ValueError(f"Invalid --min-projects: {self.min_projects}. Must be between 1 and {total_projects}.")
        if not (1 <= self.max_projects <= total_projects):
            raise ValueError(f"Invalid --max-projects: {self.max_projects}. Must be between 1 and {total_projects}.")
        if self.min_projects > self.max_projects:
            raise ValueError(f"--min-projects ({self.min_projects}) cannot be greater than --max-projects ({self.max_projects}).")

        # For each subset size in the user-defined range
        for subset_size in range(self.min_projects, self.max_projects + 1):
            for combo in itertools.combinations(project_files, subset_size):
                if self.mode == "combinations":
                    # Single folder name e.g. "proj1_proj2"
                    folder_name = "_".join(combo)
                    self.build_pdf(combo, folder_name)
                else:
                    # Permutations mode => each permutation gets its own folder
                    for perm in itertools.permutations(combo, subset_size):
                        folder_name = "_".join(perm)  # e.g. "proj1_proj2" or "proj2_proj1"
                        self.build_pdf(perm, folder_name)


def main():
    parser = argparse.ArgumentParser(description="Generate LaTeX resumes with custom project combinations or permutations.")
    parser.add_argument(
        "--mode",
        choices=["combinations", "permutations"],
        default="combinations",
        help="Build either combinations or permutations of project files. Default = combinations."
    )
    parser.add_argument(
        "--pdf_name",
        default="AliBakly.pdf",
        help="Name of the PDF file inside each output folder. Default = AliBakly.pdf"
    )
    parser.add_argument(
        "--min_projects",
        type=int,
        default=2,
        help="Minimum number of projects in each resume. Default = 2."
    )
    parser.add_argument(
        "--max_projects",
        type=int,
        default=3,
        help="Maximum number of projects in each resume. Default = 3."
    )
    args = parser.parse_args()

    builder = ResumeBuilder(
        mode=args.mode,
        pdf_name=args.pdf_name,
        min_projects=args.min_projects,
        max_projects=args.max_projects
    )
    builder.run()


if __name__ == "__main__":
    main()
