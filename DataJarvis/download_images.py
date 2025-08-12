#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载DataJarvis页面中的所有PNG图片并替换为本地路径
"""

from inspect import currentframe
import os
import re
import requests
import time
from urllib.parse import urlparse
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """创建带有重试机制的requests会话"""
    session = requests.Session()
    
    # 配置重试策略
    retry_strategy = Retry(
        total=3,  # 最多重试3次
        backoff_factor=1,  # 重试间隔
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的HTTP状态码
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def download_image(url, save_dir, session):
    """下载单个图片"""
    try:
        print(f"正在下载: {url}")
        
        # 尝试不同的SSL配置
        ssl_options = [
            {'verify': True},  # 默认SSL验证
            {'verify': False},  # 禁用SSL验证
            {'verify': True, 'timeout': 60},  # 增加超时时间
        ]
        
        for i, ssl_config in enumerate(ssl_options):
            try:
                print(f"  尝试SSL配置 {i+1}/{len(ssl_options)}...")
                response = session.get(url, timeout=30, **ssl_config)
                response.raise_for_status()
                break
            except Exception as e:
                print(f"    SSL配置 {i+1} 失败: {str(e)}")
                if i == len(ssl_options) - 1:  # 最后一次尝试
                    raise e
                time.sleep(1)  # 等待1秒后重试
        
        # 从URL中提取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # 如果没有文件名，使用URL的hash作为文件名
        if not filename or '.' not in filename:
            filename = f"image_{hash(url)}.png"
        
        # 确保文件名以.png结尾
        if not filename.endswith('.png'):
            filename += '.png'
        
        filepath = os.path.join(save_dir, filename)
        
        # 保存文件
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ 下载完成: {filename}")
        return filename
        
    except Exception as e:
        print(f"✗ 下载失败: {url}")
        print(f"  错误信息: {str(e)}")
        return None

def extract_image_urls(html_file):
    """从HTML文件中提取所有图片URL"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找所有img标签的src属性
    img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
    img_urls = re.findall(img_pattern, content)
    
    # 过滤出PNG图片URL
    png_urls = []
    for url in img_urls:
        if url.endswith('.png') or 'png' in url.lower():
            png_urls.append(url)
    
    return png_urls

def replace_image_urls(html_file, url_mapping):
    """替换HTML文件中的图片URL为本地路径"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有远程图片URL为本地路径
    for remote_url, local_filename in url_mapping.items():
        if local_filename:  # 只替换成功下载的图片
            local_path = f"./downloaded_images/{local_filename}"
            content = content.replace(remote_url, local_path)
            print(f"✓ 替换链接: {remote_url} -> {local_path}")
    
    # 保存修改后的HTML文件
    backup_file = html_file.with_suffix('.html.backup')
    print(f"备份原文件为: {backup_file}")
    os.rename(html_file, backup_file)
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✓ HTML文件已更新，图片链接已替换为本地路径")

def main():
    # 设置下载目录
    current_dir = "D:/Code/Demo/github上demo仓库/Demo/DataJarvis"
    current_dir = Path(current_dir)
    download_dir = current_dir / "downloaded_images"
    
    # 创建下载目录
    download_dir.mkdir(exist_ok=True)
    print(f"图片将下载到: {download_dir}")
    
    # HTML文件路径
    html_file = current_dir / "index.html"
    
    if not html_file.exists():
        print(f"错误: 找不到HTML文件 {html_file}")
        return
    
    # 创建会话
    session = create_session()
    
    # 提取图片URL
    print("正在解析HTML文件...")
    image_urls = extract_image_urls(html_file)
    
    if not image_urls:
        print("没有找到PNG图片")
        return
    
    print(f"找到 {len(image_urls)} 个PNG图片:")
    for i, url in enumerate(image_urls, 1):
        print(f"  {i}. {url}")
    
    # 下载图片并记录URL映射
    print(f"\n开始下载图片...")
    url_mapping = {}  # 远程URL -> 本地文件名
    
    for url in image_urls:
        filename = download_image(url, download_dir, session)
        url_mapping[url] = filename
        time.sleep(0.5)  # 添加延迟避免请求过快
    
    # 统计下载结果
    success_count = sum(1 for filename in url_mapping.values() if filename)
    total_count = len(image_urls)
    
    print(f"\n下载完成!")
    print(f"成功: {success_count}/{total_count}")
    print(f"图片保存在: {download_dir}")
    
    # 替换HTML文件中的图片链接
    if success_count > 0:
        print(f"\n开始替换HTML文件中的图片链接...")
        replace_image_urls(html_file, url_mapping)
        print(f"✓ 所有操作完成!")
    else:
        print(f"没有成功下载的图片，跳过HTML文件更新")

if __name__ == "__main__":
    main()
