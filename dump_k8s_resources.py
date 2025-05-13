import subprocess, concurrent.futures, os, shutil, zipfile, json
from tqdm import tqdm

DUMP_DIR = "k8s-dump"
ALLOWED_GROUPS = ["", "apps", "batch", "networking.k8s.io", "policy", "rbac.authorization.k8s.io", "autoscaling"]

def run_cmd(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout if result.returncode == 0 else None

def get_resources(namespaced=True):
    flag = "--namespaced=true" if namespaced else "--namespaced=false"
    result = subprocess.run(["kubectl", "api-resources", "--verbs=list", flag, "-o", "wide"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("Ошибка при получении ресурсов:", result.stderr)
        return []
    lines = result.stdout.strip().splitlines()[1:]
    resources = []
    for line in lines:
        parts = line.split()
        if len(parts) >= 4 and parts[-1] in ALLOWED_GROUPS:
            resources.append(parts[0])
    return resources

def dump_resource(resource, namespaced=True):
    safe = resource.replace("/", "_")
    out_json = os.path.join(DUMP_DIR, f"{safe}.json")
    out_desc = os.path.join(DUMP_DIR, f"{safe}.describe.txt")
    scope_flag = "-A" if namespaced else ""
    try:
        json_data = run_cmd(["kubectl", "get", resource, scope_flag, "-o", "json"])
        if not json_data:
            return None
        data = json.loads(json_data)
        if len(data.get("items", [])) == 0:
            return None
        with open(out_json, "w", encoding="utf-8") as f:
            f.write(json_data)

        desc_data = run_cmd(["kubectl", "describe", resource, scope_flag])
        if desc_data:
            with open(out_desc, "w", encoding="utf-8") as f:
                f.write(desc_data)
    except Exception as e:
        return f"Ошибка: {e}"
    return None

def dump_events():
    out = os.path.join(DUMP_DIR, "events.txt")
    try:
        events = run_cmd(["kubectl", "get", "events", "-A", "--sort-by=.metadata.creationTimestamp"])
        if events and "No resources found" not in events:
            with open(out, "w", encoding="utf-8") as f:
                f.write(events)
    except Exception as e:
        return str(e)

def zip_results():
    zip_path = "k8s-dump.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(DUMP_DIR):
            for file in files:
                full = os.path.join(root, file)
                zipf.write(full, os.path.relpath(full, DUMP_DIR))
    print(f"[✓] Архив сохранён: {zip_path}")

def main():
    if os.path.exists(DUMP_DIR):
        shutil.rmtree(DUMP_DIR)
    os.makedirs(DUMP_DIR)

    res = [(r, True) for r in get_resources(True)] + [(r, False) for r in get_resources(False)]
    print(f"[*] Начинаем сбор {len(res)} ресурсов...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        for f in tqdm(concurrent.futures.as_completed([ex.submit(dump_resource, r, n) for r, n in res]), total=len(res)):
            if f.result():
                print(f.result())

    dump_events()
    zip_results()

if __name__ == "__main__":
    main()
