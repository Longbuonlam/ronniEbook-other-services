import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse

import os
# Use path relative to the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
ratings = pd.read_csv(os.path.join(current_dir, "dataset/rating.csv"))

# Tạo ánh xạ từ UUID sang số nguyên cho user_id và book_id
user_mapping = {uid: idx + 1 for idx, uid in enumerate(ratings['UserID'].unique())}
book_mapping = {bookid: idx + 1 for idx, bookid in enumerate(ratings['BookID'].unique())}

# Tạo ánh xạ ngược từ số nguyên sang UUID cho book_id
reverse_book_mapping = {idx: bookid for bookid, idx in book_mapping.items()}

def get_book_uuid_by_index(reverse_book_mapping, index_list):
    return [reverse_book_mapping[idx] for idx in index_list]

# Áp dụng ánh xạ cho user_id và book_id
ratings['user_id'] = ratings['UserID'].map(user_mapping)
ratings['book_id'] = ratings['BookID'].map(book_mapping)


class CF(object):
    """
    class Collaborative Filtering, hệ thống đề xuất dựa trên sự tương đồng
    giữa các users với nhau, giữa các items với nhau
    """
    def __init__(self, data_matrix, k, dist_func=cosine_similarity, uuCF=1):
        """
        Khởi tạo CF với các tham số đầu vào:
            data_matrix: ma trận Utility, gồm 3 cột, mỗi cột gồm 3 số liệu: user_id, item_id, rating.
            k: số lượng láng giềng lựa chọn để dự đoán rating.
            uuCF: Nếu sử dụng uuCF thì uuCF = 1 , ngược lại uuCF = 0. Tham số nhận giá trị mặc định là 1.
            dist_f: Hàm khoảng cách, ở đây sử dụng hàm cosine_similarity của klearn.
            limit: Số lượng items gợi ý cho mỗi user. Mặc định bằng 10.
        """
        self.uuCF = uuCF  # user-user (1) or item-item (0) CF
        self.Y_data = data_matrix if uuCF else data_matrix[:, [1, 0, 2]]
        self.k = k
        self.dist_func = dist_func
        self.Ybar_data = None
        # số lượng user và item, +1 vì mảng bắt đầu từ 0
        self.n_users = int(np.max(self.Y_data[:, 0])) + 1
        self.n_items = int(np.max(self.Y_data[:, 1])) + 1

    def add(self, new_data):
        """
        Cập nhật Y_data khi có lượt rating mới.
        """
        self.Y_data = np.concatenate((self.Y_data, new_data), axis=0)

    def normalize_matrix(self):
        """
        Tính similarity giữa các items bằng cách tính trung bình cộng ratings giữa các items.
        Sau đó thực hiện chuẩn hóa bằng cách trừ các ratings đã biết của item cho trung bình cộng
        ratings tương ứng của item đó, đồng thời thay các ratings chưa biết bằng 0.
        """
        users = self.Y_data[:, 0]
        self.Ybar_data = self.Y_data.copy()
        self.mu = np.zeros((self.n_users,))
        for n in range(self.n_users):
            ids = np.where(users == n)[0].astype(np.int32)
            item_ids = self.Y_data[ids, 1]
            ratings = self.Y_data[ids, 2]
            # take mean
            m = np.mean(ratings)
            if np.isnan(m):
                m = 0  # để tránh mảng trống và nan value
            self.mu[n] = m
            # chuẩn hóa
            self.Ybar_data[ids, 2] = ratings - self.mu[n]
        self.Ybar = sparse.coo_matrix((self.Ybar_data[:, 2],
                                       (self.Ybar_data[:, 1], self.Ybar_data[:, 0])), (self.n_items, self.n_users))
        self.Ybar = self.Ybar.tocsr()

    def similarity(self):
        """
        Tính độ tương đồng giữa các user và các item
        """
        eps = 1e-6
        self.S = self.dist_func(self.Ybar.T, self.Ybar.T)

    def refresh(self):
        """
        Chuẩn hóa dữ liệu và tính toán lại ma trận similarity. (sau khi một số xếp hạng được thêm vào).
        """
        self.normalize_matrix()
        self.similarity()

    def fit(self):
        self.refresh()

    def __pred(self, u, i, normalized=1):
        """
        Dự đoán ra ratings của các users với mỗi items.
        """
        # tìm tất cả user đã rate item i
        ids = np.where(self.Y_data[:, 1] == i)[0].astype(np.int32)
        users_rated_i = (self.Y_data[ids, 0]).astype(np.int32)
        
        # Handle case where no users have rated this item
        if len(users_rated_i) == 0:
            return 0
            
        sim = self.S[u, users_rated_i]
        a = np.argsort(sim)[-self.k:]
        nearest_s = sim[a]
        
        # Fix the indexing issue by properly selecting users
        selected_users = users_rated_i[a]
        r = self.Ybar[i, selected_users].toarray().flatten()
        
        if normalized:
            # cộng với 1e-8, để tránh chia cho 0
            return np.sum(r * nearest_s) / (np.abs(nearest_s).sum() + 1e-8)

        return np.sum(r * nearest_s) / (np.abs(nearest_s).sum() + 1e-8) + self.mu[u]

    def pred(self, u, i, normalized=1):
        """
        Xét xem phương pháp cần áp dùng là uuCF hay iiCF
        """
        if self.uuCF: return self.__pred(u, i, normalized)
        return self.__pred(i, u, normalized)

    def print_list_item(self):
        for i in range(self.n_items):
            print(i)

    def recommend(self, u):
        """
        Determine all items should be recommended for user u.
        The decision is made based on all i such that:
        self.pred(u, i) > 0. Suppose we are considering items which
        have not been rated by u yet.
        """
        ids = np.where(self.Y_data[:, 0] == u)[0]
        items_rated_by_u = self.Y_data[ids, 1].tolist()
        recommended_items = []
        for i in range(self.n_items):
            if i not in items_rated_by_u:
                rating = self.__pred(u, i)
                if rating > 0:
                    recommended_items.append(i)

        return recommended_items

    def recommend_top(self, u, top_x):
        """
        Determine top 10 items should be recommended for user u.
        . Suppose we are considering items which
        have not been rated by u yet.
        """
        ids = np.where(self.Y_data[:, 0] == u)[0]
        items_rated_by_u = self.Y_data[ids, 1].tolist()
        item = {'id': None, 'similar': None}
        list_items = []

        def take_similar(elem):
            return elem['similar']

        for i in range(self.n_items):
            if i not in items_rated_by_u:
                rating = self.__pred(u, i)
                item['id'] = i
                item['similar'] = rating
                list_items.append(item.copy())

        sorted_items = sorted(list_items, key=take_similar, reverse=True)
        sorted_items.pop(top_x)
        return sorted_items
    
    
rating_matrix = ratings[['user_id', 'book_id', 'Rating']].values
cf_model = CF(rating_matrix, k=5, uuCF=1)  # Using user-user CF with 5 neighbors
cf_model.fit()

