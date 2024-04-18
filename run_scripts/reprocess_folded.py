import re
import subprocess
import os

LIMIT = 8 
def split_line_remove_number(line):
    # Remove the trailing number using regular expression
    line_without_number = re.sub(r'\s*\d+$', '', line)
    # Split the line by semicolon
    parts = line_without_number.split(';')
    return parts

def extract_number_at_end(line):
    match = re.search(r'\d+$', line)
    if match:
        return int(match.group())
    else:
        return None
    
def get_high_level_symbol(line):
    blacklisted_symbols = ['entry_SYSCALL_64', 'do_syscall_64', 'do_syscall_x64','do_syscall_x64', '__x86_indirect_thunk_rax',
                           'entry_SYSCALL_64_after_hwframe', 'strcmp', 'memmove', 'memset']
    parts = split_line_remove_number(line)
    
    parts = [part.strip() for part in parts]
    
    # shrinked_parts = parts
    # if len(parts) > 12:
    #     shrinked_parts = parts[:16]
    # shrinked_str = ';'.join(shrinked_parts)
    
    for part in parts:
        part = part.strip()
        if part not in blacklisted_symbols:
            return part, parts
        
    return parts[-1], parts

def split_to_parts(line):
    parts = split_line_remove_number(line)
    parts = [part.strip() for part in parts]
    return parts


def processing_call_chain(parts, preserved_list, black_list):
    next_match_idx = 0
    
    output_parts = []
    for i, part in enumerate(parts):
        if next_match_idx < len(preserved_list):
            if part in preserved_list[next_match_idx]:
                output_parts.append(part)
                next_match_idx += 1
            else:
                continue
        else:
            if part not in black_list:
                output_parts.append(part)
                
    output_parts = shrink_parts(output_parts)
    
    # print('input:', parts)
    # print('output:', output_parts)
    
    return output_parts


def processing_PF_handler(parts):
    preserved_list = [
        {'asm_exc_page_fault'},
        {'handle_mm_fault', 'find_vma'}
    ]
    
    black_list = {'__handle_mm_fault', 'ecpt_is_partially_built_in_2M_range', 
                'gen_pte_is_partially_built', 'pmd_alloc'}
    
    next_match_idx = 0
    
    output_parts = processing_call_chain(parts, preserved_list, black_list)
    
    # print('input:', parts)
    # print('output:', output_parts)
    
    return output_parts

def processing_syscall(parts):
    syscall = ""
    for p in parts:
        if '__x64_sys' in p:
            syscall = p
            break
        
    preserved_list = [{'entry_SYSCALL_64'}, {syscall}]
    
    if "__x64_sys_munmap" in syscall:
        preserved_list.append({'__do_munmap'})
    elif "__x64_sys_brk" in syscall:
        preserved_list.append({'__do_sys_brk'})
    elif "__x64_sys_read" in syscall:
        preserved_list.append({'ksys_read'})
    
    if syscall == "":
        preserved_list = [{'entry_SYSCALL_64'}]
    
    black_list = {'__x86_indirect_thunk_rax'}
    
    return processing_call_chain(parts, preserved_list, black_list)

def shrink_parts(parts):
    shrinked_parts = parts

    if len(parts) > LIMIT:
        shrinked_parts = parts[:LIMIT]
    return shrinked_parts


def replace_key_function(parts):
    key_function_map = {
        'pte_offset_ecpt': 'ecpt_locate_pte',
        'get_hpt_entry': 'do_locate',
        'ecpt_search_fit_entry': 'ecpt_search',

        'pmd_offset_ecpt': 'ecpt_locate_pmd',

        'ptep_get_next' : 'tentey_iter_next',
        'set_pte_at' : 'insert_pte',
        'ecpt_set_pte_at': 'ecpt_insert_pte',
                
        'gen_pte_void' : 'tentry_range_void',
        
        'gen_pte_is_partially_built' : "aspace_partial_built",
        
        'ecpt_pmd_is_partially_built' : 'ecpt_check_4KB_map'
        
    }
    
    for i, part in enumerate(parts):
        if part in key_function_map:
            parts[i] = key_function_map[part]
    return parts

def add_macro_functions(parts):
    macro_functions = {
        r'native_p*' : 'read_pte_attr',
        r'p*d_mk*' : 'write_pte_attr',
        r'pte_mk*' : 'write_pte_attr',
        r'p*d_clear*' : 'write_pte_attr',
        r'pte_clear*' : 'write_pte_attr',

        'ecpt_locate_pte' : 'locate_pte',
        'ecpt_locate_pmd' : 'locate_pte',
        'tentry_range_void' : 'thp_eligible',
    }
    
    output_parts = []
    for i, part in enumerate(parts):
        for pattern in macro_functions:
            match = re.match(pattern, part)
            if match:
                output_parts.append(macro_functions[pattern])
                break
        output_parts.append(part)

    # print('input:', parts)
    # print('output:', output_parts)

    return output_parts

def make_flame_human_readable(flame_folded_path: str):
    print(f"Make {flame_folded_path} human readable")
    readable_flame_path =  flame_folded_path + ".readable"
    global LIMIT
    if 'ecpt_always' in flame_folded_path:
        # BAD PRACTICE
        LIMIT = 8
    else:
        LIMIT = 7
    
    print(f"LIMIT: {LIMIT}")
    with open(readable_flame_path, 'w') as readable:
        with open(flame_folded_path, 'r') as file:
            for line in file:
                # high_level_key, parts = get_high_level_symbol(line)
                parts = split_to_parts(line)
                high_level_key = parts[0]
                
                number = extract_number_at_end(line)
                # print(high_level_key)
                # if  'timer' not in high_level_key:
                if 'asm_exc_page_fault' in high_level_key:
                    parts = processing_PF_handler(parts)
                if 'entry_SYSCALL_64' in high_level_key:
                    parts = processing_syscall(parts)
                else:
                    parts = shrink_parts(parts)
                
                parts = replace_key_function(parts)
                parts = add_macro_functions(parts)
                parts = shrink_parts(parts)
                print(f"{';'.join(parts).strip()} {number}", file = readable)
                    
    return readable_flame_path

def produce_flame_graph(folded_path: str):
    flamegraph_out_path = folded_path + ".svg"
    command = f"./flamegraph.pl --bgcolors \#FFFFFF --width 850 --height 20 --fontsize 15 --title \" \" {folded_path} > {flamegraph_out_path}"
    print(command)
    subprocess.run(command, shell=True, check=True)
    print("Flamegraph saved to ", flamegraph_out_path)
    
    
    return flamegraph_out_path


def reprocess_folded(flame_folded_path):
    print(f"Reprocess {flame_folded_path}")
    reprocess_flame_path =  flame_folded_path + ".reprocessed"

    with open(reprocess_flame_path, 'w') as reprocessed:
        with open(flame_folded_path, 'r') as file:
            for line in file:
                # high_level_key, parts = get_high_level_symbol(line)
                parts = split_to_parts(line)
                # high_level_key = parts[0]
                
                number = extract_number_at_end(line)
                if ('khugepaged' in parts):
                    parts = parts[parts.index('khugepaged'):]
                
                print(f"{';'.join(parts).strip()} {number}", file = reprocessed)
                    
    return reprocess_flame_path
    
    # flame_folded_path = "kernel_inst/radix_never_graphbig_bfs_walk_log.bin.kern_inst.folded"
    # readable_flame_path = make_flame_human_readable(fl

def get_high_level_distribution(flame_path):
    high_level_flame = {}
    with open(flame_path, 'r') as file:
        for line in file:
            number = extract_number_at_end(line)
            high_level_key, _ = get_high_level_symbol(line)
            if high_level_key not in high_level_flame:
                high_level_flame[high_level_key] = 0
            high_level_flame[high_level_key] += number
    
    high_level_path = flame_path + ".high_level.csv"
    print(f"Saving high level flamegraph to {high_level_path}")
    with open(flame_path + ".high_level.csv", 'w') as f:
        for key in high_level_flame:
            print(f"{key},{high_level_flame[key]}", file = f)
    return high_level_path


def reprocess_and_make_readable(flame_folded_path):
    reprocessed_flame_path = reprocess_folded(flame_folded_path)
    readable_flame_path = make_flame_human_readable(reprocessed_flame_path)
    produce_flame_graph(readable_flame_path)
    return readable_flame_path

def run_reprocess():
    folder = 'kernel_inst_loading/full_kernel_noIter_withPlace'
    path = os.path.join(folder, 'ecpt_always_graphbig_bfs_walk_log.bin.kern_inst.folded')
    reprocess_and_make_readable(path)

    folder = 'kernel_inst_loading/full_kernel_withIter_withPlace'
    path = os.path.join(folder, 'ecpt_always_graphbig_bfs_walk_log.bin.kern_inst.folded')
    reprocess_and_make_readable(path)


# def reprocess_and_get_high_level_distribution(flame_folded_path):
#     reprocessed_flame_path = reprocess_folded(flame_folded_path)
#     readable_flame_path = make_flame_human_readable(reprocessed_flame_path)
#     produce_flame_graph(readable_flame_path)
#     return get_high_level_distribution(readable_flame_path)

if __name__ == '__main__':
    
    folder = 'kernel_inst_loading/full_kernel_withIter_withPlace'
    files = [f for f in os.listdir(f'{folder}')]
    for folded_path in files:
        if folded_path.endswith('kern_inst.folded'):
            print(folded_path)
            flame_folded_path = os.path.join(f'{folder}', folded_path)
            reprocessed_flame_path = reprocess_folded(flame_folded_path)
            get_high_level_distribution(reprocessed_flame_path)

            # readable_flame_path = make_flame_human_readable(readable_flame_path)
            # produce_flame_graph(readable_flame_path)


    # # folder = 'kernel_inst_loading/full_kernel_noIter_withPlace'
    # files = [f for f in os.listdir(f'{folder}')]
    
    # for folded_path in files:
    #     # if folded_path.endswith('ecpt_never_graphbig_bfs_no_iter_walk_log.bin.folded'):
    #     if folded_path.endswith('ecpt_always_graphbig_bfs_walk_log.bin.kern_inst.folded'):
    #         print(folded_path)
    #         flame_folded_path = os.path.join(f'{folder}', folded_path)
    #         readable_flame_path = reprocess_folded(flame_folded_path)
    #         # produce_flame_graph(readable_flame_path)
    #         # flame_folded_path = os.path.join(f'{folder}', folded_path)
    #         readable_flame_path = make_flame_human_readable(readable_flame_path)
    #         produce_flame_graph(readable_flame_path)
    
    # flame_folded_path = "kernel_inst/radix_never_graphbig_bfs_walk_log.bin.kern_inst.folded"
    # readable_flame_path = make_flame_human_readable(flame_folded_path)
    # produce_flame_graph(readable_flame_path)
    