# 查看历史提交中的邮箱信息
git log --pretty=format:"%h - %an, %ae, %cd" -10

# 如果发现私有邮箱，使用以下脚本批量修改
git filter-branch -f --env-filter '
OLD_EMAIL="旧的私有邮箱"
CORRECT_EMAIL="25992899+samelltiger@users.noreply.github.com"
if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]
then
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
' --tag-name-filter cat -- --all
