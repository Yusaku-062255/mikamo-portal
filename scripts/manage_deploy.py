#!/usr/bin/env python3
"""
みかもポータル デプロイマネージャー（v0.2）

使い方:
    python scripts/manage_deploy.py prod --project-id YOUR_PROJECT_ID [--region asia-northeast1]

機能:
    - Backend をビルド・デプロイ
    - Frontend をビルド・デプロイ（Backend URLを注入）
    - Backend の CORS を Frontend URL に絞る

============================================================
実行コマンド（コピペ用）:

    export PROJECT_ID="soup-app-476708"
    export REGION="asia-northeast1"
    gcloud auth login
    gcloud config set project "$PROJECT_ID"
    cd /Users/kanemurayuusaku/mikamo_portal
    python3 scripts/manage_deploy.py prod --project-id "$PROJECT_ID" --region "$REGION"

============================================================
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def print_header(step: str, title: str) -> None:
    """ステップヘッダーを表示"""
    print("\n" + "=" * 60)
    print(f"{step}: {title}")
    print("=" * 60)


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> None:
    """コマンドを実行し、エラー時は終了"""
    print(f"\n実行中: {' '.join(cmd)}")
    try:
        # 環境変数を明示的に引き継ぐ（親プロセスから）
        env = os.environ.copy()
        subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            check=True,
            capture_output=False,  # リアルタイムで出力を見せる
            text=True,
            env=env  # 環境変数を明示的に引き継ぐ
        )
    except subprocess.CalledProcessError as e:
        print(f"\n❌ エラー: コマンドが失敗しました")
        print(f"   コマンド: {' '.join(cmd)}")
        print(f"   終了コード: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ エラー: コマンドが見つかりません: {cmd[0]}")
        print(f"   gcloud がインストールされ、PATH に含まれているか確認してください")
        sys.exit(1)


def ensure_gcloud_auth(project_id: str) -> None:
    """gcloud認証を確認"""
    print_header("Step 0", "gcloud認証確認")

    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'],
            capture_output=True,
            text=True,
            check=True
        )

        if not result.stdout.strip():
            print("❌ gcloud認証がされていません")
            print("\n以下のコマンドで認証してください:")
            print(f"  gcloud auth login")
            print(f"  gcloud config set project {project_id}")
            sys.exit(1)

        account = result.stdout.strip()
        print(f"✅ 認証済み: {account}")

    except subprocess.CalledProcessError:
        print("❌ gcloud認証の確認に失敗しました")
        sys.exit(1)


def debug_gcloud_auth(project_id: str) -> None:
    """gcloud認証情報をデバッグ出力"""
    print("\n" + "-" * 60)
    print("🔍 デバッグ: gcloud認証情報の確認")
    print("-" * 60)
    
    # 現在のアカウントを確認
    try:
        result = subprocess.run(
            ['gcloud', 'config', 'get-value', 'account'],
            capture_output=True,
            text=True,
            check=True
        )
        account = result.stdout.strip()
        print(f"現在のアカウント: {account}")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  アカウント取得エラー: {e}")
    
    # 現在のプロジェクトを確認
    try:
        result = subprocess.run(
            ['gcloud', 'config', 'get-value', 'project'],
            capture_output=True,
            text=True,
            check=True
        )
        current_project = result.stdout.strip()
        print(f"現在のプロジェクト: {current_project}")
        if current_project != project_id:
            print(f"⚠️  警告: 設定プロジェクト ({current_project}) と指定プロジェクト ({project_id}) が異なります")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  プロジェクト取得エラー: {e}")
    
    # Application Default Credentials の確認
    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'application-default', 'print-access-token'],
            capture_output=True,
            text=True,
            stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            print("✅ Application Default Credentials が設定されています")
        else:
            print("⚠️  Application Default Credentials が設定されていません")
            print("   必要に応じて以下を実行してください:")
            print("   gcloud auth application-default login")
    except Exception as e:
        print(f"⚠️  Application Default Credentials 確認エラー: {e}")
    
    print("-" * 60)


def deploy_backend(project_id: str, region: str) -> str:
    """Backendをビルド・デプロイし、URLを返す"""
    print_header("Step 1", "Backend ビルド・デプロイ")

    image_name = f"gcr.io/{project_id}/mikamo-portal-backend"
    service_name = "mikamo-portal-backend"

    # デバッグ: 認証情報を確認
    debug_gcloud_auth(project_id)

    # Cloud Build でイメージをビルド
    print(f"\n📦 イメージをビルド中: {image_name}")
    
    # 実行する完全なコマンドを表示
    build_cmd = [
        'gcloud', 'builds', 'submit', '.',
        '--project', project_id,
        '--config', 'infra/cloudbuild.backend.yaml',
        '--substitutions', f'_IMAGE_NAME={image_name}'
    ]
    print(f"\n🔍 デバッグ: 実行コマンド（完全版）")
    print(f"   {' '.join(build_cmd)}")
    
    run_command(build_cmd)

    # Cloud Run にデプロイ
    print(f"\n🚀 Cloud Run にデプロイ中: {service_name}")
    deploy_cmd = [
        'gcloud', 'run', 'deploy', service_name,
        '--project', project_id,
        '--region', region,
        '--image', image_name,
        '--platform', 'managed',
        '--allow-unauthenticated',
        '--port', '8080',
        '--set-env-vars', 'BACKEND_CORS_ORIGINS=*',  # 一旦全許可、後で絞る
        '--set-secrets', 'DATABASE_URL=MIKAMO_DB_URL:latest',
        '--set-secrets', 'JWT_SECRET_KEY=MIKAMO_JWT_SECRET:latest',
        '--set-secrets', 'OPENAI_API_KEY=MIKAMO_OPENAI_KEY:latest',
        # 初期管理者ユーザー（オプション、Secret Managerに登録されている場合のみ）
        # '--set-secrets', 'INITIAL_ADMIN_EMAIL=MIKAMO_INITIAL_ADMIN_EMAIL:latest',
        # '--set-secrets', 'INITIAL_ADMIN_PASSWORD=MIKAMO_INITIAL_ADMIN_PASSWORD:latest',
        # '--set-secrets', 'INITIAL_ADMIN_FULL_NAME=MIKAMO_INITIAL_ADMIN_FULL_NAME:latest',
        '--quiet'
    ]

    run_command(deploy_cmd)

    # URLを取得
    print(f"\n🔍 Backend URL を取得中...")
    result = subprocess.run(
        [
            'gcloud', 'run', 'services', 'describe', service_name,
            '--project', project_id,
            '--region', region,
            '--format', 'value(status.url)'
        ],
        capture_output=True,
        text=True,
        check=True
    )

    backend_url = result.stdout.strip()
    print(f"✅ Backend URL: {backend_url}")
    return backend_url


def deploy_frontend(project_id: str, region: str, backend_url: str) -> str:
    """Frontendをビルド・デプロイし、URLを返す"""
    print_header("Step 2", "Frontend ビルド・デプロイ")

    image_name = f"gcr.io/{project_id}/mikamo-portal-frontend"
    service_name = "mikamo-portal-frontend"

    # Cloud Build でイメージをビルド（VITE_API_BASE_URLをsubstitutionで渡す）
    print(f"\n📦 イメージをビルド中: {image_name}")
    print(f"   VITE_API_BASE_URL={backend_url}")
    
    # 実行する完全なコマンドを表示
    build_cmd = [
        'gcloud', 'builds', 'submit', '.',
        '--project', project_id,
        '--config', 'infra/cloudbuild.frontend.yaml',
        '--substitutions', f'_IMAGE_NAME={image_name},_VITE_API_BASE_URL={backend_url}'
    ]
    print(f"\n🔍 デバッグ: 実行コマンド（完全版）")
    print(f"   {' '.join(build_cmd)}")
    
    run_command(build_cmd)

    # Cloud Run にデプロイ
    print(f"\n🚀 Cloud Run にデプロイ中: {service_name}")
    run_command([
        'gcloud', 'run', 'deploy', service_name,
        '--project', project_id,
        '--region', region,
        '--image', image_name,
        '--allow-unauthenticated',
        '--port', '8080',
        '--platform', 'managed',
        '--quiet'
    ])

    # URLを取得
    print(f"\n🔍 Frontend URL を取得中...")
    result = subprocess.run(
        [
            'gcloud', 'run', 'services', 'describe', service_name,
            '--project', project_id,
            '--region', region,
            '--format', 'value(status.url)'
        ],
        capture_output=True,
        text=True,
        check=True
    )

    frontend_url = result.stdout.strip()
    print(f"✅ Frontend URL: {frontend_url}")
    return frontend_url


def update_backend_cors(project_id: str, region: str, frontend_url: str) -> None:
    """BackendのCORSをFrontend URLに絞る"""
    print_header("Step 3", "Backend CORS 更新")

    service_name = "mikamo-portal-backend"
    print(f"   CORS を {frontend_url} に設定")

    run_command([
        'gcloud', 'run', 'services', 'update', service_name,
        '--project', project_id,
        '--region', region,
        '--set-env-vars', f'BACKEND_CORS_ORIGINS={frontend_url}',
        '--platform', 'managed',
        '--quiet'
    ])

    print("✅ CORS の更新が完了しました")


def main():
    parser = argparse.ArgumentParser(
        description='みかもポータル デプロイマネージャー',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  export PROJECT_ID="soup-app-476708"
  export REGION="asia-northeast1"

  python scripts/manage_deploy.py prod \\
    --project-id "$PROJECT_ID" \\
    --region "$REGION"
        """
    )
    parser.add_argument(
        'env',
        help='デプロイ環境 (現時点では prod のみサポート)'
    )
    parser.add_argument(
        '--project-id',
        required=True,
        help='GCP プロジェクトID (必須)'
    )
    parser.add_argument(
        '--region',
        default='asia-northeast1',
        help='GCP リージョン (デフォルト: asia-northeast1)'
    )

    args = parser.parse_args()

    # 環境チェック
    if args.env != 'prod':
        print(f"❌ エラー: 環境 '{args.env}' はサポートされていません")
        print("   現時点では 'prod' のみサポートしています")
        sys.exit(1)

    # プロジェクトルートを取得
    global PROJECT_ROOT
    PROJECT_ROOT = Path(__file__).parent.parent

    print("=" * 60)
    print("みかもポータル v0.2 デプロイ開始")
    print("=" * 60)
    print(f"環境: {args.env}")
    print(f"プロジェクト: {args.project_id}")
    print(f"リージョン: {args.region}")

    # gcloud認証確認
    ensure_gcloud_auth(args.project_id)

    # Backend デプロイ
    backend_url = deploy_backend(args.project_id, args.region)

    # Frontend デプロイ
    frontend_url = deploy_frontend(args.project_id, args.region, backend_url)

    # CORS を更新
    update_backend_cors(args.project_id, args.region, frontend_url)

    # 完了メッセージ
    print("\n" + "=" * 60)
    print("✅ デプロイが完了しました！")
    print("=" * 60)
    print(f"\n📱 Deployed frontend URL: {frontend_url}")
    print(f"🔧 Backend URL: {backend_url}")
    print("\nこのURLを従業員に共有してください。")
    print("（最初のURLは長いですが、Google公式の安全なURLです）")
    print("=" * 60)


if __name__ == '__main__':
    main()
