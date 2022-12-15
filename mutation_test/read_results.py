import shelve

if __name__ == '__main__':
    with shelve.open("mutation_test/mutation_cov_results/store") as results:
        for key, val in results.items():
            print(key, val)