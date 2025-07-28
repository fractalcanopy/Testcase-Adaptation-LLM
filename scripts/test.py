from write_matching_projects import check_build

if __name__ == "__main__":
    check_build(
        project_path="data/projects/LightCouch",
        build_system="maven",
        command=["mvn", "clean", "test-compile"],
    )
