from argparse import ArgumentParser, FileType


def main():
    p = ArgumentParser()
    p.add_argument('input', type=FileType('r'))
    p.add_argument('output', type=FileType('w'))
    args = p.parse_args()

    input_file = args.input
    output_file = args.output

    for line in input_file:
        if '\\n' in line:
            line = line.replace('\\n', '\n')
        output_file.write(line)
    
    input_file.close()
    output_file.close()


if __name__ == '__main__':
    main()
