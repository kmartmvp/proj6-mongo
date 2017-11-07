import nose
from flask_main import create_handler
from flask_main import delete
from flask_main import collection
import os


def assert_create():
    # Count docs: http://fistfvck.sakura.ne.jp/MongoDB-manual-master/reference/method/cursor.count.html#cursor.count
    num_of_memos = collection.find().count()
    create_handler()

    assert collection.find().count() == num_of_memos + 1


def assert_delete():
    num_of_memos = collection.find().count()
    flask_main.delete()

    assert collection.find().count() == num_of_memos - 1